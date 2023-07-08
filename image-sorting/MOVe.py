"""
MOVe.py

If sort images using a program like PhotoSift,
you may subsequently have all your live photo MOV's
remain in the original folder, unsorted, and you feel real silly

Instead of moving them manually after the fact,
let's automate it as much as possible!
"""


# Imports
from glob import glob
from os import path, getcwd
from shutil import move
from shutil import Error
from pathlib import Path
from os.path import join, dirname
from argparse import ArgumentParser
from typing import List

parser = ArgumentParser(
    prog="MOVe.py"
)

parser.add_argument(
    "--source", "--source-glob", "--src", "-sc", "-s",
    help="The glob to be used for the live photos/MOV files. Default value is based on the current directory",
    default=getcwd() + "/**/*.MOV"
)

parser.add_argument(
    "--destination", "--dest", "-d",
    help="""
        The top-most directory of where the destination/sorted photos are.
        For example: if the sorted photos are in D:/Pictures/Travel
                                               & D:/Pictures/Friends/Sora
                     ... the value should be D:/Pictures/
        """,
        default="D:/Pictures/"
)

parser.add_argument(
    "--duplicate-folder", "--duplicate", "-df",
    help="What folder to store duplicates in if the destination already has a corresponding FILE.mov",
    default="D:/Pictures/Duplicates/"
)

parser.add_argument(
    "--excludes", "-e",
    nargs="*",
    help="What folders to not look in for destinations",
    required=False
    )

args = parser.parse_args()

SOURCE = args.source
DESTINATION = args.destination
DUPLICATE_FOLDER = args.duplicate_folder
EXCLUDES = args.excludes

# Functions
def move_file_if_not_exists(src, dest):
    """
    Move {src} to {dest}. Both are meant to be full paths, including filename

    If this is not possible, allow the following options as a backup:
        0: Exit/cancel
        1: Add " (1)" to the destination filename
        2: Move to a specified duplicate folder
    
    """
    try:
        move(src, dest)
    except Error:
        source = Path(src)
        
        alternative_filename = "{0} (1){1}".format(source.stem, source.suffix)
        alternative_dest = join(dirname(dest), alternative_filename)
        
        duplicate_dest = join(DUPLICATE_FOLDER, source.name)

        print("{0} already exists at {1}".format(source.name, dest))
        print("0: Exit")
        print("1: Rename & copy to source (new dest: {})".format(alternative_dest))
        print("2: Move to duplicate folder (new dest: {})".format(duplicate_dest))

        prompt = int(input("Select [0]: ") or 0)
        if prompt == 1:
            print("Renaming & copying")
            move_file_if_not_exists(src, alternative_dest)
            print("Renamed & copied!")
        elif prompt == 2:
            print("Moving to duplicate folder...")
            move_file_if_not_exists(src, duplicate_dest)
        else:
            print("Exiting...")
            exit()

def not_in_excludes(item):
    for exclude in excludes:
        if exclude.samefile(item):
            return False
    return True

excludes: List[Path] = []
for exclude in EXCLUDES:
    excludes.append(Path(exclude))

files_to_move = glob(SOURCE, recursive=True)
for mov in files_to_move:
    # Double check if file
    if path.isfile(mov):
        filename = path.splitext(path.basename(mov))[0]
        results = glob(DESTINATION + "/**/" + filename + "*[!MOV]", recursive=True)
        results = list(filter(not_in_excludes, results))
        
        amount_of_results = len(results)
        if amount_of_results == 0:
            print("No image found for " + filename)
        
        elif amount_of_results > 1:
            print("Too many results for " + filename)
            print("Results: ")
            i = 0
            for result in results:
                print("{0}: {1}".format(i, result))
                i += 1
                
            selected_index = int(input("Select: "))
            dest_dir = path.dirname(results[selected_index])
            print("Selected! Moving {0} to {1}".format(filename, dest_dir))
            move_file_if_not_exists(mov, dest_dir)

        elif amount_of_results == 1:
            dest_dir = path.dirname(results[0])
            print("Found! Moving {0} to {1}".format(filename, dest_dir))
            move_file_if_not_exists(mov, dest_dir)


