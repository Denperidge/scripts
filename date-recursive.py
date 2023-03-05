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

apply = "--apply" in args


def prepend(filename):
    path = Path(filename).absolute() 
    if path.name.startswith("IMG_"):

        # st_mtime is last modified
        file_date = datetime.fromtimestamp(path.stat().st_mtime)

        new_path = path.with_name(file_date.strftime(DATE_FORMAT_STRING) + path.name)
        print(f"""

            Renaming:
                    {path}
                --> {new_path}
            """)
        
        if apply:
            # I think this was for some iphone weird stuff
            patch(path)
            path.rename(new_path)


    else:
        print(f"NOT processing {path.name}")

def undo(filename):
    path = Path(filename).absolute()
    should_be_undo_ed = search(NAME_FORMATTED, path.name, RegexFlag.IGNORECASE)
    if should_be_undo_ed is not None:
        to_remove = should_be_undo_ed.group(0)
        new_path = path.with_name(path.name.replace(to_remove, ""))

        print(f"""

            Renaming:
                    {path}
                --> {new_path}
            """)
        if apply:
            path.rename(new_path)

    else:
        print(f"SKIPPING {path.name}")


def patch(path=None):
    if path is None:
        path = Path(DIRECTORY[:DIRECTORY.index("**")]).absolute()
        path = str(path) + "/"

    print(f"Running exiftool on {path}")
    if apply:
        # "Filecreatedate > filemodifydate instead of datetimeoriginal > filemodifydate because some images don't have datetimeoriginal
        system(f'exiftool -r "-FileCreateDate<DateTimeOriginal" "-FileModifyDate<FileCreateDate" "{path}"')




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

