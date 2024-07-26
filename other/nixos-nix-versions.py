from urllib.request import urlopen, HTTPError
from re import compile, DOTALL, MULTILINE

# NOTE: Is this, correct? Did 22.11 downgrade? I might be looking at the wrong branch

nixos_versions = [    
    "24.05",
    "23.11",
    "23.05",
    "22.11",
    "22.05",
    "21.11",
    "21.05",
    "20.09",
    "20.03",
    "19.09",
    "19.03",
    "18.09",
    "18.03",
    "17.09",
    "17.03",
    "16.09",
    "16.03",
    "15.09",
    "14.12",
    "14.04",
    "13.10"
]
re_version = compile(r"^ *?(nixStable| stable).*?({\n|).*?nix(_|\-)(?P<version>[_\d\.]*)", MULTILINE)
re_older_version = compile(r" *name.*?nix-(?P<version>(\d|\.)*)")

table =  "|  NixOS version  |  Nix version  |\n"
table += "| --------------- | ------------- |\n"


for nixos_version in nixos_versions:
    try:
        response = urlopen(f"https://raw.githubusercontent.com/NixOS/nixpkgs/release-{nixos_version}/pkgs/tools/package-management/nix/default.nix")
        data = response.read().decode("utf-8")
    except HTTPError as e:
        print("Error with " + nixos_version)
        print(e)
        continue

    try:
        if not nixos_version.startswith("14") and not nixos_version.startswith("13"):
            nix_version = re_version.search(data).group("version").replace("_", ".")
        else:
            nix_version = re_older_version.search(data).group("version")

    except AttributeError as e:
        print("Error with " + nixos_version)
        print(e)
        continue


    table += f"|      {nixos_version}      |    {nix_version.ljust(7)}    |\n"
print(table)
