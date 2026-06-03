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
CACHE_PATH = Path("proton-ge-cache.json")
CACHE = dict()

scroll_pos = 0  # (Start) scroll position

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

def cache_load():
    global CACHE
    # Load cache if needed
    if not CACHE_PATH.exists():  # TODO check cache age
        CACHE = {"releases": {}}
        with CACHE_PATH.open("w", encoding="utf-8") as file:
            dump(CACHE, file)
    else:
        with CACHE_PATH.open("r", encoding="utf-8") as cache_file:
            CACHE = load(cache_file)

def cache(key: str, subkey: str=None, value: any=None) -> any:
    if value is None:
        # Get from cache
        if not subkey:
            return CACHE.get(key, None)
        else:
            return CACHE[key][subkey]
    else:
        # Write to cache
        if not subkey:
            CACHE[key] = value
        else:
            CACHE[key][subkey] = value
        with CACHE_PATH.open("w", encoding="utf-8") as cache_file:
            dump(CACHE, cache_file)
        return value

def cache_request(url: str):
    # If the requested url is not in the cache 
    if url not in cache("releases").keys():
        # Request...
        with urlopen(url) as req:
            # ...and cache
            cache("releases", url, req.read().decode("utf-8"))
    
    # Return data from cache
    return cache("releases", url)
        

def get_steam_compattools_dir() -> Path:
    # Get from cache if possible
    cached_value = cache("target")
    if cached_value:
        # Parse cache
        cached_value = Path(cached_value)
        # Return if the path exists
        if cached_value.exists():
            return cached_value
        # Otherwise, continue
    
    # Check default path
    default_path: Path = Path().home().joinpath("s.steam/steam/compatibilitytools.d/")
    if default_path.exists():
        return default_path
    else:
        # Otherwise, ask to create path
        print(f"Destination proton folder doesn't exist! Create {default_path}?")
        create_folder = input("[Y/n]: ").lower() != "n"
        
        if create_folder:
            from os import makedirs
            makedirs(default_path)
            return default_path
        else:
            # Otherwise, ask for a path
            print("Please enter the path to your steam compatibilitytools.d directory")
            path = Path(input("Path: "))
            if path.exists():
                # Cache the custom path as str
                cache("target", value=str(path.absolute()))
                return path  # & return the Path
            else:
                raise FileNotFoundError("The provided path does not exist")

class Release():
    def __init__(self, raw_data: object):
        # Metadata
        self.name = raw_data["tag_name"]
        print(f"Parsing {self.name}...")

        self.url = raw_data["html_url"]

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

    def install(self, target_dir: Path):
        target = target_dir.joinpath(self.targz["name"])
        
        print(f"Please wait! Downloading {self.name} to {target}...")
        urlretrieve(self.targz["url"], target)

        checksum_matches = checksum_is_equal_to(target, self.get_checksum())
        if not checksum_matches:
            print("The downloaded file has a different checksum than is expected from the GitHub release. Cancel installation?")
            if input("[Y/n]: ").lower() != "n":
                raise ValueError("Abandonded installation due to checksum problems")

        command = f"tar -xzvf {target.name}"
        print(f"Running {command} in {target_dir}...")
        run(command, shell=True, cwd=target_dir, encoding="UTF-8")

        print(f"Done installing {self.name} to {target_dir}")
        print(f"Removing {target.name}...")
        remove(target)
        print("Done! Exiting...")

    def __str__(self):
        return self.name

def get_proton_ge_releases(page_size: int, page: int=1) -> list[Release]:
    releases = loads(cache_request(RELEASES_API_URL + f"?per_page={page_size}&page={page}"))
    return list(map(lambda release: Release(release), releases))

# TUI
def xdg_open(target: str):
    run(f"xdg-open '{target}'", shell=True, capture_output=True, start_new_session=True)

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
    elif key in ["O", "o"]:
        return "open"
    elif key in ["T", "t"]:
        return "target"
    else:
        return None

page = 1
def select_release(screen: curses.window, target_dir: Path, releases: list[Release]) -> Release:
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
    screen.addstr(f"\tSCROLL POS: {scroll_pos}\tLOADED RELEASES: {len(releases)}\t[T] Open target directory\t\t\t\n\n", curses.A_REVERSE)


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
    elif action == "open":
        xdg_open(releases[scroll_pos].url)
    elif action == "target":
        xdg_open(target_dir.absolute())
    elif action == "exit":
        keep_running = False
        return None

    screen.refresh()
    screen.clear()

    if keep_running:
        return select_release(screen, target_dir, releases)
    
def start_tui(target_dir: Path) -> Release:  # TODO open on github
    return curses.wrapper(select_release, target_dir, [])
    
if __name__ == "__main__":
    cache_load()
    target_dir = get_steam_compattools_dir()
    release = start_tui(target_dir)
    if release:
        release.install(target_dir)
# TODO ask to clear cache
# TODO optimise cache 
