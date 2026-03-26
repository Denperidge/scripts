# Denperidge's scripts

Some scripts that I have written that are too essential for a gist but too small for a repo!

## Scripts for...
### Development
| Script name | Status | Description |
| ----------- | ------ | ----------- |
| [dconf-to-nixos](development/dconf-to-nixos) | ✅ Recently used | Turn a dconf directory into declarative NixOS settings |
| [forgejo-github.py](development/forgejo-github.py) | 🛠️ Needs work | Sync your GitHub repos to Forgejo! |
| [gh-card-png.sh](development/gh-card-png.sh) | ✅ Recently tested | Leverages the gh-card project to create PNG repo cards |
| [python-installer.py](development/python-installer.py) | ⏰ Old script | Altinstall any Python3 version straight from the source, with no fuss |
| [quick-multiple-ssh-key-setup.py](development/quick-multiple-ssh-key-setup.py) | ⏰ Old script | Quickly SSH key & ./.ssh/config |

### ⏰ Old image sorting scripts
| Script name | Description |
| ----------- | ----------- |
| [date-recursive.py](image-sorting/date-recursive.py) | Recursively rename your images based on EXIF metadata |
| [MOVe.py](image-sorting/MOVe.py) | Move your .MOV live photos after their still photo equivalent |
| [DELduplicates.py](image-sorting/DELduplicates.py) | I forgot what I used this for but it was in the folder where MOVe.py was! |


## Discussions
### Design decisions
Every script in this repo is...
- ...self-containing: the runtime requirements and documentation can be found in the top-most comment
- ... too small for a dedicated repo

### Why a repo?
Originally I had some of these as gists. But I've noticed updating it there isn't really super efficienct, and it felt super disorganised. Now I can use shortcuts or symlinks towards a central place on my computer, and I can move it between devices. Gists kinda seem to work best with snippets of code mostly; but they fall apart even in terms of having people possibly PR changes.

## License
All the code here is released under the [MIT License](LICENSE)!
