from pathlib import Path
from urllib.request import urlopen, urlretrieve
from subprocess import run
from json import load, loads, dump
from typing import Callable
from os import remove
import curses

"""
Download & extract proton-ge to the correct Steam location
with a simple terminal script

Requirements: any existing python3 version, tar command

Developed for non-flatpak Linux,
but should work on other setups with some adapting
"""

REPO = "GloriousEggroll/proton-ge-custom"
RELEASES_API_URL = f"https://api.github.com/repos/{REPO}/releases"
CACHE = Path("proton-ge-cache.json")

scroll_pos = 0  # (Start) scroll position
screen = None  # Curses screen, for use with 

def checksum_is_equal_to(file: Path, checksum: str) -> bool:
    if run("sha512sum --help", shell=True, capture_output=True).returncode != 0:
        print("WARNING: Could not find sha256sum in PATH. Skipping checksum verification")
        return True
    else:
        command = f"sha512sum '{file.name}'"
        print(f"Calculating checksum using {command}...")
        file_checksum = run(command, shell=True, cwd=file.parent, capture_output=True).stdout.decode("utf-8")
        print(f"sha512sum from local file: '{file_checksum}'")
        return file_checksum == checksum

def cache_request(url: str):
    # Check if cache exists
    cache_exists = CACHE.exists()
    if not cache_exists:  # TODO check cache age
        cache = {"releases": {}}
        with CACHE.open("w", encoding="utf-8") as file:
            dump(cache, file)
    else:
        # Read cache
        with CACHE.open("r", encoding="utf-8") as cache_file:
            cache = load(cache_file)

    # If the cache is empty or the requested url is not in the cache 
    if not cache_exists or url not in cache["releases"].keys():
        # Request...
        with urlopen(url) as req:
            cache["releases"][url] = req.read().decode("utf-8")
        # ...and cache
        with CACHE.open("w", encoding="utf-8") as cache_file:
            dump(cache, cache_file)
            
    # Return req as-is from cache        
    return cache["releases"][url]
        

def get_steam_compattools_dir() -> Path:
    default_path: Path = Path().home().joinpath(".steam/steam/compatibilitytools.d/")
    if default_path.exists():
        return default_path
    else:
        print(f"Destination proton folder doesn't exist! Create {default_path}?")
        create_folder = input("[Y/n]: ").lower() != "n"
        
        if create_folder:
            from os import makedirs
            makedirs(default_path)
            return default_path
        else:
            print("Please enter the path to your steam compatibilitytools.d directory")
            path = Path(input("Path: "))
            if path.exists():
                return path
            else:
                raise FileNotFoundError("The provided path does not exist")

class Release():
    def __init__(self, raw_data: object):
        # Metadata
        self.name = raw_data["tag_name"]
        print(f"Parsing {self.name}...")

        # Asset parsing
        #assets = list(filter(
        #    lambda asset: asset["name"].split(".", 1)[1] not in ("tar.zst"), raw_data["assets"]))
        #assert len(assets) == 2
        assets = raw_data["assets"]

        for asset in assets:
            asset_name: str = asset["name"]
            if asset_name.endswith(".tar.gz"):
                # Is proton itself
                self.targz = {
                    "name": asset["name"],
                    "url": asset["browser_download_url"]
                }
            elif asset_name.endswith(".sha512sum"):
                self.checksum = asset["browser_download_url"]
            elif asset_name.endswith(".tar.zst") or asset_name == "SHA256SUMS":
                continue
            else:
                raise NotImplementedError(f"Unexpected file (format) from file {asset_name}")
    
    def get_checksum(self):
        checksum = cache_request(self.checksum)
        
        print(f"sha512sum from upstream: '{checksum}'")
        return checksum

    def install(self):
        steam_dir = get_steam_compattools_dir()
        target = steam_dir.joinpath(self.targz["name"])
        
        print(f"Please wait! Downloading {self.name} to {target}...")
        urlretrieve(self.targz["url"], target)

        checksum_matches = checksum_is_equal_to(target, self.get_checksum())
        if not checksum_matches:
            print("The downloaded file has a different checksum than is expected from the GitHub release. Cancel installation?")
            if input("[Y/n]: ").lower() != "n":
                raise ValueError("Abandonded installation due to checksum problems")

        command = f"tar -xzvf {target.name}"
        print(f"Running {command} in {steam_dir}...")
        run(command, shell=True, cwd=steam_dir, encoding="UTF-8")

        print(f"Done installing {self.name}! Removing {target.name}...")
        remove(target)
        print("Done! Exiting...")

    def __str__(self):
        return self.name

def get_proton_ge_releases(page_size: int, page: int=1) -> list[Release]:
    releases = loads(cache_request(RELEASES_API_URL + f"?per_page={page_size}&page={page}"))
    return list(map(lambda release: Release(release), releases))

# TUI
def key_is_action(key: str):
    """ Converts multiple keys to the same string, to allow multiple controls for the same function """

    # Arrow up, Page Up, Arrow Up (Git Bash), Page Up (Git Bash), w, W, z, Z, 8
    if key in ["KEY_UP", "KEY_PPAGE", "KEY_A2", "KEY_A3", "w", "W", "z", "Z", "8"]:
        return "up"
    # Arrow down, Page Down, Arrow down (Git Bash), Page Down (Git Bash), s, S, 5, 2
    elif key in ["KEY_DOWN", "KEY_NPAGE", "KEY_C2", "KEY_C3", "s", "S", "5", "2"]:
        return "down"
    elif key in ["I", "i"]:
        return "install"
    elif key in ["E", "e"]:
        return "exit"
    else:
        return None

page = 1
def select_release(screen: curses.window, releases: list[Release]) -> Release:
    global scroll_pos
    global page
    """Main curses CLI function. Displays releases and allows to scroll through & select them"""
    keep_running = True

    scroll_size = screen.getmaxyx()[0] - 5  # -5 for ui elements
    
    if len(releases) == 0:  # Initialize
        releases = get_proton_ge_releases(scroll_size*3, page)
    """
    - 1 (scroll pos)
    - 2
    - 3
    ------- scroll size 3, initial view. After this scroll pos, load
    - 4
    - 5
    - 6 (6 loaded releases)
    """
    if scroll_pos == len(releases) - scroll_size + 1:
        page += 1  # TODO can scroll_size schange unexpelctedly?
        releases += get_proton_ge_releases(page_size=scroll_size * 3, page=page)

    screen.addstr("\t[ARROW_UP/PAGE_UP] Move up\t[I] Install\t[O] Open on GitHub\t\n", curses.A_REVERSE)
    screen.addstr("\t[ARROW_DOWN/PAGE_DOWN] Move down\t[E] Exit\t\t\t\n", curses.A_REVERSE)
    screen.addstr(f"\tSCROLL POS: {scroll_pos}\tLOADED RELEASES: {len(releases)}\tPAGE: {page}\t\t\t\n\n", curses.A_REVERSE)


    for release in releases[scroll_pos:scroll_pos+scroll_size]:
        if releases.index(release) == scroll_pos:
            screen.addstr("> " + str(release), curses.A_STANDOUT)
        else:
            screen.addstr(str(release))
        screen.addstr("\n")

    screen.refresh()

    action = key_is_action(screen.getkey())
    if action == "up" and scroll_pos > 0:
        scroll_pos -= 1
    elif action == "down" and scroll_pos < len(releases):
        scroll_pos += 1
    elif action == "install":
        return releases[scroll_pos]
    elif action == "exit":
        keep_running = False
        return None

    screen.refresh()
    screen.clear()

    if keep_running:
        return select_release(screen, releases)
    
def start_tui() -> Release:  # TODO open on github
    return curses.wrapper(select_release, [])  # TODO remove global screen var
    
if __name__ == "__main__":
    #releases = get_proton_ge_releases()
    release = start_tui()
    if release:
        release.install()

# TODO ask to clear cache

# TODO further pages of releases