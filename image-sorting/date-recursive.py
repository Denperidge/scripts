from glob import glob
from pathlib import Path
from sys import argv
from os import system
from re import search, RegexFlag
from datetime import datetime

DIRECTORY = "D:/Pictures/**/*"
DATE_FORMAT_STRING = "%Y%m%d_%H%M%S__"  # == yyyyMMdd_HHmmss__
NAME_FORMATTED = r"[^a-z]{1,}_{2}"
MODES = ["prepend", "undo", "patch"]

args = [arg.lower() for arg in argv]

apply = "--apply" in args  # Whether to not do a dry run
allow_rename_original_when_undoing = "--arowu" in args
patch_before_prepend = "--patch" in args
filename_startswith = "--startswith" in args  # Optional parameter of yyyyMMdd

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
    


def prepend(filename):
    path = Path(filename).absolute() 
    if path.name.startswith("IMG_"):

        if apply and patch_before_prepend:
                patch(path, extra_tags="")

        # st_mtime is last modified
        file_date = datetime.fromtimestamp(path.stat().st_mtime)

        new_path = path.with_name(file_date.strftime(DATE_FORMAT_STRING) + path.name)
        print(f"""

            Renaming:
                    {path}
                --> {new_path}
            """)
        
        if apply:            
            path.rename(new_path)


    else:
        print(f"NOT processing {path.name}")

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
        path = str(path) + "/"
    
    """
    if not filename_startswith:
        filename_filter = "IMG_"

    if filename_startswith:
        filename_filter = filename_startswith_str
    """

    print(f"Running exiftool on {path}")
    if apply:
        # "Filecreatedate > filemodifydate instead of datetimeoriginal > filemodifydate because some images don't have datetimeoriginal
        print(system(f'exiftool -if "$filename=~/IMG_/" -ee {extra_tags} "-FileCreateDate<TrackCreateDate" "-FileCreateDate<MediaCreateDate" "-FileCreateDate<TrackCreateDate" "-FileCreateDate<CreateDate" "-FileCreateDate<EXIF:DateTimeOriginal" "-FileCreateDate<DateTimeOriginal" "-FileModifyDate<FileCreateDate" "{path}"'))
        



print(
    f"""
    This script can:
        {MODES[0]}: prepend {DATE_FORMAT_STRING} to files
        {MODES[1]}: remove that prepend
        {MODES[2]}: normalize metadata from iCloud
    """)


mode = input("Select mode: ").lower().strip()

if mode not in MODES:
    exit(0)

# Prepend
if mode == MODES[0]:
    handle_file = prepend
# Undo prepend
elif mode == MODES[1]:
    handle_file = undo
# Patch iCloud metadata
elif mode == MODES[2]:
    patch()
    exit(0)


files = glob(DIRECTORY, recursive=True)
for file in files:
    handle_file(file)

