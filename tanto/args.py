import sys, os
from unittest.mock import Mock
from argparse import *
from tanto.tanto_utility import *
from tanto import _keybindings
import tanto

def mkVersion():
    name = os.path.basename(sys.argv[0])
    w = name + " v" + tanto.get_tanto_version() + "\n"
    w += """Copyright (C) 2024 Marius Gerdes
This is free software; see the source for copying conditions.  There is NO
warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE."""
    return w
    
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
    (x, y) = guessScreenXY()
    p = ArgumentParser(description= "Lightweight, speech empowered audio and video editor.",
                       formatter_class=ArgumentDefaultsHelpFormatter)
    p.add_argument("--version", action='version', version=mkVersion())
    p.add_argument("directory", type=str, nargs='?', default=".", help="Directory to edit audio and video files in. Tanto will consider this its project directory.")
    p.add_argument("--xres", type=int, default=x, help="X-Resolution for windowed mode.")
    p.add_argument("--yres", type=int, default=y, help="Y-Resolution for windowed mode.")
    p.add_argument("-r", "--rate", type=int, default=None, help="Rate of speech for the TTS engine. The exact impact of the value depends on the underlying engine used, but often it is words-per-minute.")
    p.add_argument("-e", "--engine", type=str, choices=["spd-say", "espeak", "say", "*platform*"], default="*platform*", help="The TTS engine used throughout the program. Only a limited set is supported currently. If you choose a particular one, make sure it is available on your platform. The default of *platform* will automatically pick an engine according to your operating system.")
    p.add_argument("-i", "--volume", type=str, default=None, help="Set the volume (or intensity) for the TTS engine.")
    p.add_argument("--fullscreen", action=BooleanOptionalAction, default=False, help="Start in fullscreen mode.")
    p.add_argument("--theme", type=str, default="", help="Path to a json theme file to customize the GUI appearance.")

    return p
