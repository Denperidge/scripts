#!/usr/bin/env -S pipx run
from anytype import Anytype, Object
from readchar import readkey

"""
Quick & dirty script to decrease Discord server
load by archiving pinned messages to anytype
"""

# pipx metadata
# /// script
# dependencies = ["anytype-client", "readchar"]
# ///

def select(items: list, subkey: str=None):
    for i in range(0, len(items)):
        value = items[i] if not subkey else items[i][subkey]
        print(f"{i}: {items[i]}")
    print("Selection: ")
    return items[int(readkey())]


if __name__ == "__main__":
    anytype  = Anytype()
    anytype.auth()

    space = select(anytype.get_spaces())

    object_type = select(space.get_types(), "name")
    print(object_type)