from urllib.request import urlopen, urlretrieve
from html.parser import HTMLParser
from subprocess import run, PIPE
from tarfile import open
from os import remove
from shutil import rmtree
import curses

""" A script to install other Python versions next to your existing installation without having to do things because I hate doing things """


""" FUNCTIONALITY

Simply run `python3 python-installer.py, and use the CLI to select a release!
The script will automatically...
- Download the tgz
- Extract it
- Run ./configure - make - make altinstall
- Remove the previously downloaded source files

Without any external dependencies!
"""

""" KNOWN ISSUES
- No threading; the script freezes during an install, and status only gets updated when pressing buttons

"""

# Constants
PYTHON_DOMAIN = "https://www.python.org"
SOURCE_DOWNLOADS = f"{PYTHON_DOMAIN}/downloads/source/"
RELEASE_STARTSWITH = "/downloads/release/"
RELEASES_SCROLL_SIZE = 5

all_python_releases = []  # Array with all pyt
scroll_pos = 0  # (Start) scroll position
screen = None  # Curses screen, for use with 

class Release():
    """Class to hold Python Release info"""
    def __init__(self, name:str=None, url:str=None) -> None:
        self.name = name
        self.url = url
    
    @property
    def tag(self):
        return self.name.split(" -", 1)[0].replace(" ", "-")
    
    @property
    def tgz(self):
        return self.tag + ".tgz"

    
    def install(self):
        update_status(f"Downloading {self.url}...")

        urlretrieve(self.url, self.tgz)

        update_status(f"Extracting {self.tgz}...")
        with open(self.tgz, "r") as tarfile:
            tarfile.extractall(path=".")
            dir = tarfile.getmembers()[0].name
        
        update_status(f"Extracted to {dir}")

        for command in ["./configure", "make", "make altinstall"]:
            update_status(f"Running {command}...")
            run(command, cwd=dir, stdout=PIPE, stderr=PIPE)
        

        update_status(f"Cleaning up tmp files for {self.tag}")
        rmtree(dir)
        remove(self.tgz)
            
        update_status(f"Installed {self.tag}!")
    
    def __str__(self) -> str:
        return f"{self.name} ({self.url})"

    def __repr__(self) -> str:
        return self.__str__()

class PythonDownloadParser(HTMLParser):
    """HTMLParser class to extract Python Release info from the website"""
    new_release = None

    def handle_starttag(self, tag: str, attrs: list) -> None:
        for key, value in attrs:
            if key == "href":
                if value.startswith(RELEASE_STARTSWITH):
                    self.new_release = Release()
                elif value.endswith(".tgz"):
                    self.new_release.url = value
                    all_python_releases.append(self.new_release)
                    self.new_release = None

    def handle_data(self, data: str) -> None:
        if self.new_release:
            if self.new_release.name is None:
                self.new_release.name = data

def key_is_action(key: str):
    """ Converts multiple keys to the same string, to allow multiple controls for the same function """

    # Arrow up, Page Up, Arrow Up (Git Bash), Page Up (Git Bash), w, W, z, Z, 8
    if key in ["KEY_UP", "KEY_PPAGE", "KEY_A2", "KEY_A3", "w", "W", "z", "Z", "8"]:
        return "up"
    # Arrow down, Page Down, Arrow down (Git Bash), Page Down (Git Bash), s, S, 5, 2
    elif key in ["KEY_UP", "KEY_NPAGE", "KEY_C2", "KEY_C3", "s", "S", "5", "2"]:
        return "down"
    elif key in ["I", "i"]:
        return "install"
    elif key in ["E", "e"]:
        return "exit"
    else:
        return None
    
def update_status(status):
    """Clears the curses CLI and displays the provided string"""
    screen.clear()
    screen.addstr(status)
    screen.refresh()

def select_installs(curses_screen):
    """Main curses CLI function. Displays releases and allows to scroll through & select them"""
    global scroll_pos, screen
    screen = curses_screen
    keep_running = True

    
    screen.addstr("\t[ARROW_UP/PAGE_UP] Move up\t\t[I] Install\t\n", curses.A_REVERSE)
    screen.addstr("\t[ARROW_DOWN/PAGE_DOWN] Move down\t[E] Exit\t\n\n", curses.A_REVERSE)

    for version in all_python_releases[scroll_pos: scroll_pos+RELEASES_SCROLL_SIZE]:
        if all_python_releases.index(version) == scroll_pos:
            screen.addstr(str(version), curses.A_BLINK)
        else:
            screen.addstr(str(version))
        screen.addstr("\n")

    screen.refresh()

    action = key_is_action(screen.getkey())
    if action == "up" and scroll_pos > 0:
        scroll_pos -= 1
    elif action == "down" and scroll_pos < len(all_python_releases):
        scroll_pos += 1
    elif action == "install":
        all_python_releases[scroll_pos].install()
    elif action == "exit":
        keep_running = False

    screen.refresh()
    screen.clear()

    if keep_running:
        select_installs(screen)

# Download the releases
with urlopen(SOURCE_DOWNLOADS) as site:
    parser = PythonDownloadParser()
    parser.feed(str(site.read()))

# Start the CLI
curses.wrapper(select_installs)
