#!/usr/bin/env -S pipx run

# pipx metadata
# /// script
# dependencies = ["requests"]
# ///

from time import sleep
from os import makedirs
from os.path import dirname, realpath, join, isfile
from re import match, search
from json import dump, load
from requests import get

APP_ID_RANGE = range(0, 200)

SCRIPT_DIR = dirname(realpath(__file__))
CACHE_FILE = join(SCRIPT_DIR, ".steam-id-cache.json")

REQUEST_URL = "https://store.steampowered.com/app/"
TITLE_REGEX = r"<title>(?P<title>.*?)( on Steam|)</title>"



#makedirs(CACHE_DIR, exist_ok=True)
if isfile(CACHE_FILE):
    with open(CACHE_FILE, "r", encoding="utf-8") as file:
        cache = load(file)
else:
    cache = dict()

def cache_and_print(req_url, title, setCache=True):
    if setCache:
        cache[req_url] = title
    if title is not False:
        print("[INFO]: {0} == {1}".format(req_url, title))
    else:
        print("[INFO]: No game found for {}".format(req_url))

def app_info_from_steam(app_id, req_url):
    try:
        req = get(req_url)
        history_count = len(req.history)

        if history_count < 1:
            search_for_title = search(TITLE_REGEX, req.text)
            if search_for_title is not None:
                title = search_for_title.group("title")
                if title is not None:
                    cache_and_print(req_url, title)
                else:
                    raise ValueError("[WARN]: Could not find title group for appId {}".format(app_id))
            else:
                raise ValueError("[WARN]: Could not find title element for appId {}".format(app_id))

        elif history_count == 1 and req.history[0].status_code == 302 and req.url == "https://store.steampowered.com/":
            cache_and_print(req_url, False)
        else:
            print(req.history)
            raise NotImplementedError("[ERR]: Didn't expect more than 2 redirects")
    except NotImplementedError as e:
        req.close()
        exit(1)
    except ValueError as e:
        print(e)
    finally:
        req.close()
        
    
if __name__ == "__main__":
    for app_id in APP_ID_RANGE:
        req_url = join(REQUEST_URL, str(app_id))
        if req_url in cache:
            print("[INFO]: {} found in cache".format(req_url))
            cache_and_print(req_url, cache[req_url], False)
            continue
        else:
            print("[INFO]: {} not found in cache".format(req_url))
            app_info_from_steam(app_id, req_url)
            sleep(1.2)
    
    with open(CACHE_FILE, "w", encoding="utf-8") as file:
        dump(cache, file)
