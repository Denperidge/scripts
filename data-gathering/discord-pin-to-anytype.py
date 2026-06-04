#!/usr/bin/env -S pipx run
from anytype import Anytype, Object, Property
from readchar import readkey
from typing import Callable
from pprint import pprint
import curses

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

# ----- CONSTANTS -----
actions = {}  # TUI controls, populated in start_tui
scroll_pos = 0  # (Start) scroll position
scroll_size = None  # Global var for consistent scroll size post-curses screen init


# ----- TUI -----

def setup_action_keys(action: str, keys: list[str], transform: Callable=None):
    global actions
    for key in keys:
        actions[key] = action

def init_tui():
    # Arrow up, Page Up, Arrow Up (Git Bash), Page Up (Git Bash), w, W, z, Z, 8
    setup_action_keys("up", ["KEY_UP", "KEY_PPAGE", "KEY_A2", "KEY_A3", "w", "W", "z", "Z", "8"])

    # Arrow down, Page Down, Arrow down (Git Bash), Page Down (Git Bash), s, S, 5, 2
    setup_action_keys("down", ["KEY_DOWN", "KEY_NPAGE", "KEY_C2", "KEY_C3", "s", "S", "5", "2"])
    setup_action_keys("exit", ["e", "E"])
    setup_action_keys("confirm", ["\n"])

def _select(screen: curses.window, title: str, items: list, transform: Callable):
    """Main curses CLI function. Displays items and allows to scroll through & select them"""
    global actions, scroll_size, scroll_pos, page

    if scroll_size is None:
        scroll_size = screen.getmaxyx()[0] - 5  # -5 for ui elements
    
    show_from = scroll_pos
    show_to = scroll_pos + scroll_size
    if scroll_pos != 0:
        show_from -= 1
        show_to -= 1

    screen.addstr(" [ARROW_UP/PAGE_UP] Move up\t\t[ENTER] Confirm  \n", curses.A_REVERSE)
    screen.addstr(" [ARROW_DOWN/PAGE_DOWN] Move down\t        \n", curses.A_REVERSE)
    screen.addstr(f" {title}\tSCROLL POS: {scroll_pos}\t\n\n", curses.A_REVERSE)

    for item in items[show_from:show_to]:
        value = item if not transform else transform(item)
        if items.index(item) == scroll_pos:
            screen.addstr("> " + value, curses.A_STANDOUT)
        else:
            screen.addstr(value)
        screen.addstr("\n")

    screen.refresh()

    action = actions[screen.getkey()]
    if action == "up" and scroll_pos > 0:
        scroll_pos -= 1
    elif action == "down" and scroll_pos < len(items):
        scroll_pos += 1
    elif action == "confirm":
        screen.refresh()
        screen.clear()
        return items[scroll_pos]
    elif action == "exit":
        screen.refresh()
        screen.clear()

        exit()

    screen.refresh()
    screen.clear()

    return _select(screen, title, items, transform)

def select(title: str, items: list, transform: Callable=None):
    global scroll_pos
    scroll_pos = 0
    return curses.wrapper(_select, title, items, transform)

if __name__ == "__main__":
    init_tui()

    anytype  = Anytype()
    anytype.auth()

    space = select(title="Select space", items=anytype.get_spaces(), transform=lambda space: space.name)

    types = space.get_types()
    quote_type = select("Select quote type", items=types, transform=lambda objtype: objtype.name)
    template = select("Select quote template", quote_type.get_templates(), lambda template: template.name)

    person_type = select("Select person type", items=types, transform=lambda objtype: objtype.name)
    person = select("Select person", space.search("", type=person_type, limit=30), lambda person: person.name)


    obj = Object()
    obj.add_type(quote_type)
    obj.name = "Test"
    obj.icon = None
    obj.template_id = template.id

    # Method 1: doesn't error, also doesn't assign values
    obj.date = "02/03/2026"  # Date property
    obj.people = [ person ]  # Multiselect property

    # Method 2: crashes with ValueError Format not supported
    properties = space.get_properties()
    prop_date = select("Select custom date property", items=properties, transform=lambda prop: prop.name)
    prop_person = select("Select custom people/person property", items=properties, transform=lambda prop: prop.name)
    prop_date.value = "02/06/2026"
    prop_person.value = [ person ]
    obj.properties["date"] = prop_person
    obj.properties["people"] = prop_person

    # Method 3: crashes with ValueError Format not supported
    properties = space.get_properties()
    prop_date = select("Select custom date property", items=properties, transform=lambda prop: prop.name)
    prop_person = select("Select custom people/person property", items=properties, transform=lambda prop: prop.name)
    prop_date.value = "02/06/2026"
    prop_person.value = [ person ]
    obj.properties["date"] = prop_person
    obj.properties["people"] = prop_person
    
    
    created = space.create_object(obj, quote_type)


    pprint(vars(obj))
    pprint(vars(created))
    print(created.properties)
    print(f"Created {created.name}")