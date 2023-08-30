import os, sys

# Disable print
def blockPrint():
    sys.stdout = open(os.devnull, 'w')

# Enable print
def enablePrint():
    sys.stdout = sys.__stdout__

def blockErr():
    sys.stderr = open(os.devnull, 'w')


def enableErr():
    sys.stderr = sys.__stderr__
    

blockPrint()
import pygame
from pygame.locals import *
from pygame_gui.core import ObjectID
import pygame_gui
enablePrint()


class TantoGui():
    def __init__(self, res=(0,0), manager=None):
        self.manager = manager
        self.xres = res[0]
        self.yres = res[1]


    def drawWorkspaces(self, currentWorkspace, workspaces):
        pass

    def drawTracks(self, tracks, currentTrack, currentClip):
        pass
