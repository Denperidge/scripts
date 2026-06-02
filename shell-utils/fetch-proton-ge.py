from pathlib import Path
from urllib.request import urlopen
from subprocess import run
from json import load
import curses

"""
Download & extract proton-ge to the correct Steam location
with a simple terminal script

Developed for Linux, but should work on other OS's
"""

REPO = "GloriousEggroll/proton-ge-custom"
RELEASES_API_URL = f"https://api.github.com/repos/{REPO}/releases"
RELEASES_SCROLL_SIZE = 5

scroll_pos = 0  # (Start) scroll position
screen = None  # Curses screen, for use with 

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
                self.targz = asset["url"]
            elif asset_name.endswith(".sha512sum"):
                self.checksum = asset["url"]
            elif asset_name.endswith(".tar.zst") or asset_name == "SHA256SUMS":
                continue
            else:
                raise NotImplementedError(f"Unexpected file (format) from file {asset_name}")
        
    def __str__(self):
        return self.name

def get_proton_ge_releases() -> list[Release]:
    with urlopen(RELEASES_API_URL) as req:
        releases = load(req)
    
    return list(map(lambda release: Release(release), releases))



def get_steam_compattools_dir():
    Path().home()


def download_release():
    pass

def checksum_is_equal_to(file: Path, ):
    if run("sha256sum --help", shell=True).returncode != 0:
        print("WARNING: Could not find sha256sum in PATH. Skipping checksum verification")
        return True
    else:
        print("Calculating checksum...")
        return False


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
    
    screen.addstr("\t[ARROW_UP/PAGE_UP] Move up\t\t[I] Install\t\n", curses.A_REVERSE)
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
        all_python_releases[scroll_pos].install()
        start_cli()
        return
    elif action == "exit":
        keep_running = False

    screen.refresh()
    screen.clear()

    if keep_running:
        select_release(screen, releases)
    
def start_tui(releases: list[Release]):
    curses.wrapper(select_release, releases)

if __name__ == "__main__":
    releases = get_proton_ge_releases()

    start_tui(releases)