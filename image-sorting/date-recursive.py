from glob import glob
from pathlib import Path
from sys import argv
from os import system
from subprocess import check_output
from re import search, RegexFlag
from datetime import datetime

DIRECTORY = "D:/Pictures/**/*"
DATE_FORMAT_STRING = "%Y%m__"  # == yyyyMM__, previously yyyyMMdd_HHmmss__
NAME_FORMATTED = r"[^a-z]{1,}_{2}"
MODES = ["prepend", "undo", "shorten", "patch"]

ARG_ALLOWDIFF = "--allowdiff"

args = [arg.lower() for arg in argv]
del args[0]  # Remove script location

# If the first arg is a MODE, select it
try:
    if args[0] in MODES:
        mode = args[0]
    else:
        mode = None
except IndexError:
    mode = None

provided_path = None
for arg in args:
    if "/" in arg or "\\" in arg:
        provided_path = Path(arg)
        break
if provided_path is None:
    provided_path = DIRECTORY        



apply = "--apply" in args  # Whether to not do a dry run
allow_rename_original_when_undoing = "--arowu" in args
patch_before_prepend = "--patch" in args
filename_startswith = "--startswith" in args  # Optional parameter of yyyyMMdd
always_patch_videos = "--apv" in args
allow_differing_dates_for_same_stem = ARG_ALLOWDIFF in args

if filename_startswith:
    try:
        next_arg = args[args.index("--startswith") + 1]

        # if the arg is just a next arg, instead of a value
        if next_arg.startswith("-"):
            raise IndexError
        
        filename_startswith_str = next_arg
        
    except IndexError:
        today = datetime.now()
        filename_startswith_str = today.strftime(DATE_FORMAT_STRING.split("_")[0])
    
    filename_startswith_regex = filename_startswith_str + ".*?_.*?" + NAME_FORMATTED
    print(f"Only processing files that start with specified regex. Regex: " + filename_startswith_str + " / " + filename_startswith_regex)
    

previous_old_stem = None
previous_new_stem = None
def prepend(filename):
    global previous_old_stem, previous_new_stem
    
    path = Path(filename).absolute() 
    if path.name.startswith("IMG_") and not path.name.endswith("_original"):

        if apply and patch_before_prepend:
                patch(path, extra_tags="")

        # st_mtime is last modified
        file_date = datetime.fromtimestamp(path.stat().st_mtime)

        new_path = path.with_name(file_date.strftime(DATE_FORMAT_STRING) + path.name)



        if not allow_differing_dates_for_same_stem and previous_new_stem is not None:
            if previous_old_stem == path.stem and new_path.stem != previous_new_stem:
                print(f"The new path ({new_path.stem}) would be different to the rename done with the same name before ({previous_new_stem})")
                print(f"Either run again with {ARG_ALLOWDIFF}, or check the dates of your files!")
                exit(1)
                

        print("new path: " + new_path.stem)
        previous_new_stem = new_path.stem
        previous_old_stem = path.stem

        print(f"""

            Renaming:
                    {path}
                --> {new_path}
            """)

        if apply:
            path.rename(new_path)


    else:
        print(f"NOT processing {path.name}")

def shorten():
    length = int(input("Shorten prefix to length: "))
    files = glob("**/*__*", recursive=True)
    for fileglob in files:
        file = Path(fileglob)
        
        before_prefix, after_prefix = file.name.split("__", maxsplit=1)
        
        new_prefix = before_prefix[:length]

        new_name = file.with_name(new_prefix + "__" + after_prefix)

        if str(new_name) == str(file.name):
            print("No prefix to shorten, skipping " + file.name)
            continue
        
        print(f"{fileglob} -> {new_name}")

        if apply:
            file.rename(new_name)

def undo(filename):
    path = Path(filename).absolute()

    if not filename_startswith:
        filename_regex = NAME_FORMATTED
    if filename_startswith:
        filename_regex = filename_startswith_regex

    should_be_undo_ed = search(filename_regex, path.name, RegexFlag.IGNORECASE)

    if should_be_undo_ed is not None:
        to_remove = should_be_undo_ed.group(0)
        new_path = path.with_name(path.name.replace(to_remove, ""))

        print(f"""

            Renaming:
                    {path}
                --> {new_path}
            """)
        if apply:
            try:
                path.rename(new_path)
                return new_path
            except FileExistsError as e:
                if allow_rename_original_when_undoing:
                    print(f"""
                        Already exists: {new_path}
                        Renaming original, redoing undo to {path}
                    """)
                    new_path.rename(new_path.with_stem(new_path.stem + "-1"))
                    undo(path)
                else:
                    raise e

    else:
        print(f"SKIPPING {path.name}")


def patch(path=None, extra_tags="-r"):
    if path is None:
        path = Path(DIRECTORY[:DIRECTORY.index("**")]).absolute()
        path = Path(str(path) + "/")
    else:
        path = Path(path)
    
    """
    if not filename_startswith:
        filename_filter = "IMG_"

    if filename_startswith:
        filename_filter = filename_startswith_str
    """

    print(f"Running exiftool on {path}")
    if apply:
        
        has_needed_metadata = get_attributes(path, '"-TrackCreateDate" "-TrackModifyDate" "-MediaCreateDate" "-MediaModifyDate" "-CreateDate" "-ModifyDate" "-DateTimeOriginal"')
        is_video = "video" in get_attributes(path, "-MimeType")

        if always_patch_videos and is_video:
            has_needed_metadata = False

        # If the file doesn't have the needed metadata, look for a file that does
        if not has_needed_metadata:
            print("File lacks needed metadata, extracting from sibling")


            if is_video:
                attributes_to_assign = '-api QuickTimeUTC "-TrackCreateDate={0}" "-TrackModifyDate={0}" "-MediaCreateDate={0}" "-MediaModifyDate={0}" "-CreateDate={0}" "-ModifyDate={0}"'
            else:
                attributes_to_assign = '-api QuickTimeUTC "-DateTimeOriginal={0}"'
            
            # Remove date thing
            name_without_prepend = get_name_without_prepend(path)
            sibling_selector = str(path.with_name(f'*{name_without_prepend}*[!{path.suffix}]'))

            print("Searching using " + sibling_selector)

            siblings = glob(sibling_selector)
            if len(siblings) == 0:
                print("No siblings found, don't patch")
                return
            if len(siblings) > 1:
                print("More siblings found than expected! Will try to check if one can be found with the same model")
                original_model = get_attributes(path, "-s -s -s -Model")
                print(original_model)

                for sibling in siblings:
                    print(get_attributes(sibling, "-s -s -s -Model"))
                siblings_with_the_same_model = [sibling for sibling in siblings if get_attributes(sibling, "-s -s -s -Model") == original_model and not sibling.endswith("original")]

                if len(siblings_with_the_same_model) == 0:
                    print("No siblings found with the same model. Abort.")
                    exit(1)
                elif len(siblings_with_the_same_model) > 1:
                    print("Too many siblings with the same model. Trying to find one with an identical name.")
                    siblings_with_the_same_model_and_exact_name = [sibling for sibling in siblings_with_the_same_model if get_name_without_prepend(sibling) == name_without_prepend]
                    if len(siblings_with_the_same_model_and_exact_name) == 0:
                        print("No siblings found with the same model & exact name. Aborting.")
                        exit(1)
                    elif len(siblings_with_the_same_model_and_exact_name) > 1:
                        print("Too many siblings with the same model & exact name. Aborting.")
                        exit(1)
                    else:
                        sibling = siblings_with_the_same_model_and_exact_name[0]
                        print(f"Found sibling with same model & name: {sibling}")
                else:
                    sibling = siblings_with_the_same_model[0]
            else:
                sibling = siblings[0]
            # Ensure it's patched
            patch(sibling, "")

            create_date = get_attributes(sibling, "-FileCreateDate").split(":", 1)[1].strip()
            print(attributes_to_assign.format(create_date))

            system(f'exiftool {attributes_to_assign.format(create_date)} "{path}"')
        
        attributes_to_assign = ''


        if is_video:
            attributes_to_assign += '-api QuickTimeUTC '
            attributes_to_assign += '"-FileCreateDate<TrackCreateDate" "-FileModifyDate<TrackModifyDate" '
            attributes_to_assign += '"-FileCreateDate<MediaCreateDate" "-FileModifyDate<MediaModifyDate" '
            attributes_to_assign += '"-FileCreateDate<CreateDate" "-FileModifyDate<ModifyDate" '
        else:
            attributes_to_assign += '"-FileCreateDate<DateTimeOriginal" "-FileModifyDate<DateTimeOriginal" '

        # "Filecreatedate > filemodifydate instead of datetimeoriginal > filemodifydate because some images don't have datetimeoriginal
        system(f'exiftool -if "$filename=~/IMG_/" -ee {extra_tags} {attributes_to_assign} "{path}"')
        
def get_attributes(path, attributes):
    return str(check_output(f'exiftool {attributes} "{path}"').decode("utf-8")).strip()

def get_name_without_prepend(path):
    path = Path(path)
    return path.stem.split("__")[1] if "__" in path.stem else path.stem

print(
    f"""
    This script can:
        {MODES[0]}: prepend {DATE_FORMAT_STRING} to files
        {MODES[1]}: remove that prepend
        {MODES[2]}: shorten set prefixes
        {MODES[3]}: normalize metadata from iCloud
    """)

if mode is None:
    mode = input("Select mode: ").lower().strip()

if mode not in MODES:
    exit(0)

# Prepend
if mode == MODES[0]:
    handle_file = prepend
# Undo prepend
elif mode == MODES[1]:
    handle_file = undo
elif mode == MODES[2]:
    shorten()
    exit(0)
# Patch iCloud metadata
elif mode == MODES[3]:
    patch(str(provided_path))
    exit(0)


files = glob(str(provided_path), recursive=True)
for file in files:
    handle_file(file)

