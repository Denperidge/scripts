from glob import glob
from multiprocessing.reduction import duplicate
from os import path, mkdir
from shutil import move

duplicate_folder = "Duplicates/"
if not path.isdir(duplicate_folder):
    mkdir(duplicate_folder)
# This doesn't check its own folder tho so like watchout n stuff

files = glob("Duplicates/*", recursive=True)
for file in files:
    # Double check if file
    if path.isfile(file):
        filename = path.splitext(path.basename(file))[0]
        results = glob("D:/Pictures/**/" + filename + "*", recursive=True)

        results_duplicate = results
        for result in results_duplicate:
            #print(path.dirname(path.abspath(result)) + " == " + path.dirname(path.abspath(file)))
            if path.dirname(path.abspath(result)) == path.dirname(path.abspath(file)):
                results.remove(result)
        

        
        amount_of_results = len(results)
        if amount_of_results == 0:
            print("No match found for " + filename)
            move(file, "iCloud Photos/")
        elif amount_of_results > 1:
            print("Duplicate found for " + filename)
            #move(file, duplicate_folder)

            
            


