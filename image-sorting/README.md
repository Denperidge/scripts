# Image sorting
## [date-recursive.py](date-recursive.py)
Recursively rename your images based on metadata!

*Requirements:* Python3, exiftool in path

| Modes   | Description                            |
| ------- | -------------------------------------- |
| prepend | prepend {DATE_FORMAT_STRING} to files  |
| undo    | remove that prepend                    |
| patch   | normalize metadata from iCloud         |


| Startup argument      | Description |
| --------------------- | ----------- |
| --apply               | In *all*: Apply changes. If not provided, script will do a dry run. |
| --arowu               | In *undo*: When provided, if there already is a file in the directory with the post-undo name, rename the file that was already in that directory to `NAME-1`. Afterwards, retry undo | 
| --patch               | In *prepend*: patch iCloud metadata of the file before prepending it |
| --startswith `STRING` | In *undo*: undo only if the filename starts with `STRING`. Useful when undoing a rename of a specific date |
| --apv                 | In *patch* or *prepend --patch*: force video files to be patched, even if they already have the required metadata |
| --allow-diff          | In *prepend*: by default, if two files with the same original stem (for example, img_0001.jpg & img_0001.mov) would get different prepends (thus having different datetime metadata), the script will report this and then abort. Enabling this flag will override this behaviour, and allow the script to continue even with differences in prepends |

Example usages:
```bash
python3 date-recursive.py  # Base usage, uses interactive and default defined DIRECTORY
python3 date-recursive.py patch D:/Pictures/@Photos/ --apply  # Uses --aply arg. Non-interactive, defines mode and path  

python3 date-recursive.py undo --apply --startswith 202209  # Undo the prepend of files starting with 202209
```


## [DELduplicates.py](DELduplicates.py)
I forgot what I used this for but it was in the folder where MOVe.py was!

*Requirements:* Python3

## [MOVe.py](MOVe.py)
(i)Phones now often take pictures in .JPG/.PNG as well as .MOV. So now I use Photosift to sort the images, and then run MOVe.py to move the .MOV's towards them!

*Requirements:* Python3

