#!/usr/bin/env -S pipx run
from anytype import Anytype, Object
from readchar import readkey
from typing import Callable

"""
Quick & dirty script to decrease Discord server
load by archiving pinned messages to anytype,
adding the contents to a quote type & linking it to a person type

Relies on your quote type having a `People` and `Date`
"""

# pipx metadata
# /// script
# dependencies = ["anytype-client", "readchar"]
# ///

def select(items: list, multichar=False, transform: Callable=None):
    for i in range(0, len(items)):
        value = items[i] if not transform else transform(items[i])
        print(f"{i}: {value}")
    print("Selection: ")
    selected_index = readkey() if not multichar else input()
    return items[int(selected_index)]


if __name__ == "__main__":
    anytype  = Anytype()
    anytype.auth()

    space = select(anytype.get_spaces(), transform=lambda space: space.name)

    types = space.get_types()
    print("Select quote type")
    quote_type = select(types, True, lambda objtype: objtype.name)
    print("Select people/person type")
    person_type = select(types, True, lambda objtype: objtype.name)

    person = select(space.search("", type=person_type, limit=30), lambda person: person.name)

    obj = Object()
    obj.name = "Test"
    obj.icon = ""
    obj.Date = "2026-06-02"
    obj.People = [person]
    space.create_object(obj, quote_type)
    
    print(f"Created {obj.name}")