from glob import glob
from os import path, getcwd
from shutil import move
from shutil import Error
from pathlib import Path
from os.path import join, dirname

BASE_DIR = "D:/Pictures/"

def move_if_not_exists(src, dest):
    try:
        move(src, dest)
    except Error:
        source = Path(src)
        
        copy_filename = "{0} (1){1}".format(source.stem, source.suffix)
        copy_dest = join(dirname(dest), copy_filename)
        
        duplicate_dest = join(duplicate_folder, source.name)

        print("{0} already exists at {1}".format(source.name, dest))
        print("0: Exit")
        print("1: Rename & copy to source (new dest: {})".format(copy_dest))
        print("2: Move to duplicate folder (new dest: {})".format(duplicate_dest))

        prompt = int(input("Select [0]: ") or 0)
        if prompt == 1:
            print("Renaming & copying")
            move_if_not_exists(src, copy_dest)
            print("Renamed & copied!")
        elif prompt == 2:
            print("Moving to duplicate folder...")
            move_if_not_exists(src, duplicate_dest)
        else:
            print("Exiting...")
            exit()

with open("MOVe.exclude.txt", "a+"):
    pass

excludes = []
with open("MOVe.exclude.txt", "r") as file:
    lines = file.readlines()
    for line in lines:
        excludes.append(line.strip())

def not_in_excludes(item):
    for exclude in excludes:
        if exclude in item:
            return False
    return True
    



print("Exclude list: " + str(excludes))

duplicate_folder = BASE_DIR + "/Q/"
movs = glob(getcwd() + "/iCloud Photos/*.MOV", recursive=True)
for mov in movs:
    # Double check if file
    if path.isfile(mov):
        filename = path.splitext(path.basename(mov))[0]
        results = glob(BASE_DIR + "/**/" + filename + "*[!MOV]", recursive=True)
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
            move_if_not_exists(mov, dest_dir)

        elif amount_of_results == 1:
            dest_dir = path.dirname(results[0])
            print("Found! Moving {0} to {1}".format(filename, dest_dir))
            move_if_not_exists(mov, dest_dir)


