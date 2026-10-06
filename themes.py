THEMES = {
    "cyan":   {"accent": "cyan",           "dim": "grey50", "ok": "green",        "err": "red",        "user": "bright_green"},
    "purple": {"accent": "medium_purple1", "dim": "grey50", "ok": "green",        "err": "red",        "user": "plum1"},
    "mono":   {"accent": "white",          "dim": "grey42", "ok": "white",        "err": "bright_red", "user": "white"},
    "amber":  {"accent": "dark_orange",    "dim": "grey50", "ok": "yellow",       "err": "red",        "user": "orange3"},
    "matrix": {"accent": "green",          "dim": "grey35", "ok": "bright_green", "err": "red",        "user": "green"},
    "rose":   {"accent": "pink1",          "dim": "grey50", "ok": "green",        "err": "red",        "user": "light_pink1"},
}

def get(name):
    return THEMES.get(name, THEMES["cyan"])

def names():
    return list(THEMES.keys())
