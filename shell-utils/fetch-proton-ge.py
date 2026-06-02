from pathlib import Path
from urllib.request import urlopen, urlretrieve
from subprocess import run
from json import load, dump
from tempfile import TemporaryFile
import curses

"""
Download & extract proton-ge to the correct Steam location
with a simple terminal script

Developed for Linux, but should work on other OS's
"""

REPO = "GloriousEggroll/proton-ge-custom"
RELEASES_API_URL = f"https://api.github.com/repos/{REPO}/releases"
RELEASES_SCROLL_SIZE = 5
CACHE = Path("proton-ge-cache.json")

scroll_pos = 0  # (Start) scroll position
screen = None  # Curses screen, for use with 

def checksum_is_equal_to(file: Path, checksum: str):
    if run("sha512sum --help", shell=True).returncode != 0:
        print("WARNING: Could not find sha256sum in PATH. Skipping checksum verification")
        return True
    else:
        print("Calculating checksum...")
        file_checksum = run(f"sha512sum '{file.absolute()}'", shell=True, capture_output=True).stdout
        print(f"Checksum: '{file_checksum}'")
        exit()

def cache_request(url: str):
    # Check if cache exists
    cache_exists = CACHE.exists()
    if not cache_exists:  # TODO check cache age
        with CACHE.open("w", encoding="utf-8") as file:
            dump({"releases": []}, file)
    else:
        # Read cache
        with CACHE.open("r", encoding="utf-8") as cache_file:
            cache = load(cache_file)

    # If the cache is empty or the requested url is not in the cache 
    if not cache_exists or url not in cache["releases"].keys():
        # Request...
        with urlopen(url) as data:
            cache["releases"][url] = req
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
                self.targz = asset["browser_download_url"]
            elif asset_name.endswith(".sha512sum"):
                self.checksum = asset["browser_download_url"]
            elif asset_name.endswith(".tar.zst") or asset_name == "SHA256SUMS":
                continue
            else:
                raise NotImplementedError(f"Unexpected file (format) from file {asset_name}")
    
    def get_checksum(self):
        checksum = cache_request(self.checksum).read().decode("utf-8")
        
        print(f"Expected checksum: '{checksum}'")
        return checksum

    def install(self):
        self.get_checksum()

    def __str__(self):
        return self.name

def get_proton_ge_releases() -> list[Release]:
    releases = load(cache_request(RELEASES_API_URL))
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

def select_release(screen: curses.window, releases: list[Release]):
    global scroll_pos
    """Main curses CLI function. Displays releases and allows to scroll through & select them"""
    keep_running = True

    scroll_size = screen.getmaxyx()[0] - 4  # -4 for ui elements
    
    screen.addstr("\t[ARROW_UP/PAGE_UP] Move up\t\t[I] Install\t\t[O] Open on GitHub\t\n", curses.A_REVERSE)
    screen.addstr("\t[ARROW_DOWN/PAGE_DOWN] Move down\t[E] Exit\t\n\n", curses.A_REVERSE)

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
        curses.endwin()
        releases[scroll_pos].install()
        input()
        start_tui(releases)
        return
    elif action == "exit":
        keep_running = False

    screen.refresh()
    screen.clear()

    if keep_running:
        select_release(screen, releases)
    
def start_tui(releases: list[Release]):  # TODO open on github
    curses.wrapper(select_release, releases)  # TODO remove global screen var

if __name__ == "__main__":
    releases = get_proton_ge_releases()

    start_tui(releases)