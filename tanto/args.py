import sys, os
from unittest.mock import Mock
from argparse import *
from tanto import _keybindings


def makeHelpText():
    name = os.path.basename(sys.argv[0])
    w = name + " doesn't work with project files. " + name + " works with files and directories. You may want to create a 'project directory', by creating a new directory and copying video and audio files you wish to edit into it, then invoking " + name + " with the directory as argument.\n\nBelow is a list of keybindings and commands inside " + name + ".\n"
    cats = _keybindings.categories
    d = {c : [] for c in cats}
    d[_keybindings.C_SEEK].append(("0-9", "Seek to position at nth-percentile of clip. So 1 jumps to 10%, 5 to 50% and so on. 0 is a synonym for CTRL+a."))
    d[_keybindings.C_WORKSPACE].append(("F1 - F10", "Switch to workspace."))
    d[_keybindings.C_WORKSPACE].append(("CTRL+0-9", "Send selected track to nth workspace. So CTRL+1 sends a track to workspace 1, accessible with F1, CTRL+5 workspace 5, and so on."))
    for (key, f, c, v) in _keybindings.stdKeybindings(Mock()):
        d[c].append((key, v))

    for cat in cats:
        w += "["+cat+"]\n"
        indent = 10
        for (key, desc) in d[cat]:
            padding = " " * (indent - len(key))

            w += "  " + key + padding + " - " + desc + "\n"
        w += "\n"
    return w

def makeArgParser():
    p = ArgumentParser(description="lightweight, speech empowered audio and video editor",
                       formatter_class=RawDescriptionHelpFormatter,
                       epilog=makeHelpText())
    p.add_argument("directory", type=str, default=".", help="Directory to edit audio and video files in. Tanto will consider this its project directory.")
    p.add_argument("--xres", type=int, default=1024, help="X-Resolution for windowed mode.")
    p.add_argument("--yres", type=int, default=768, help="Y-Resolution for windowed mode.")
    p.add_argument("--fullscreen", action=BooleanOptionalAction, default=False, help="Start in fullscreen mode.")
    p.add_argument("--theme", type=str, default="", help="Path to a json theme file to customize the GUI appearance.")

    return p
