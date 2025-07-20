#!/usr/bin/env -S pipx run

"""
14-04-2019: Jan-Piet Mens
  - Original script
  - https://jpmens.net/2019/04/15/i-mirror-my-github-repositories-to-gitea/

20-07-2025: Denperidge
  - Forgejo rename
  - Documentation
  - pipx
  - ConfigParser
  - Changed repo name logic
  - Attempts at migrating issues/releases... (excluding Wiki)
  - Optional INCLUDE_FORKS & REPO_NAME_REPLACE

Usage:
--------
  1. Save forgejo.github.py locally
  2. Create `forgejo-github.conf` in the same directory.
     See below for default contents
  3. Get access tokens
     Forgejo:
       - https://git.example.com/user/settings/applications
       - Enable repository read and write, user read
     GitHub:
       - https://github.com/settings/personal-access-tokens/new
       - Repository Access: as desired
       - Pull Requests: Read
       - Issues: Read
       - Contents: Read
  3. Run `chmod +x forgejo-github.py`
  4. Run `./forgejo-github.py`


forgejo-github.conf template:
-----------------------------
FORGEJO_URL=https://git.example.com
FORGEJO_TOKEN=your_token_here

GITHUB_USERNAME=your_username_here
GITHUB_TOKEN=another_token_here

# Optional, remove leading # to enable
#INCLUDE_FORKS=1  # Mirror forks. Defaults to 0 (False), set to 1 to enable
#REPO_NAME_REMOVE=OrganisationName-  # In final repo name, remove occurances of provided string
"""

# pipx metadata
# /// script
# dependencies = ["requests", "PyGithub"]
# ///

from github import Github, Auth		# https://github.com/PyGithub/PyGithub
import requests
from configparser import ConfigParser, UNNAMED_SECTION
import json
import sys
import os

config = ConfigParser(allow_unnamed_section=True)
config.read("forgejo-github.conf")
config = config[UNNAMED_SECTION]

forgejo_url = f"{config["FORGEJO_URL"]}/api/v1"
forgejo_token = config["FORGEJO_TOKEN"]

github_username = config["GITHUB_USERNAME"]
github_token = config["GITHUB_TOKEN"]

include_forks = bool(int(config["INCLUDE_FORKS"])) if "INCLUDE_FORKS" in config else False
repo_name_remove = config["REPO_NAME_REMOVE"] if "REPO_NAME_REMOVE" in config else False

session = requests.Session()        # Gitea
session.headers.update({
    "Accept": "application/json",
    "Content-type"  : "application/json",
    "Authorization" : "token {0}".format(forgejo_token),
})

r = session.get("{0}/user".format(forgejo_url))
if r.status_code != 200:
    print("Cannot get user details", file=sys.stderr)
    exit(1)

forgejo_uid = json.loads(r.text)["id"]

gh = Github(auth=Auth.Token(github_token))
repos = gh.get_user().get_repos()

for repo in repos:
    if (include_forks or not repo.fork) and github_username in repo.owner.login:
        if repo.owner.login == github_username:
            repo_name = repo.name
        else:
            repo_name = repo.full_name.replace("/", "-")
        if repo_name_remove:
            repo_name = repo_name.replace(repo_name_remove, "")

        m = {
            "repo_name"         : repo_name,
            "clone_addr"        : repo.clone_url,
            "mirror"            : True,
            "private"           : repo.private,
            "uid"               : forgejo_uid,
            "lfs"               : True,
            "labels"            : True,
            "issues"            : True,
            "pull_requests"     : True,
            "releases"          : bool(repo.get_releases().totalCount),
            #"wiki"              : repo.has_wiki,
            "milestones"        : bool(repo.get_milestones().totalCount)
        }
        if repo.description:
            m["description"] = repo.description


        if repo.private:
            m["auth_username"]  = github_username
            m["auth_password"]  = "{0}".format(github_token)

        jsonstring = json.dumps(m)

        print(f"Migrating {m['repo_name']}")
        r = session.post("{0}/repos/migrate".format(forgejo_url), data=jsonstring)
        if r.status_code != 201:            # if not CREATED
            if r.status_code == 409:        # repository exists
                continue
            print(r.status_code, r.text, jsonstring)
            exit(1)