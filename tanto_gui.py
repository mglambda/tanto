import os, sys
from tanto_utility import *

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
        self.windows = {}
        self.currentWindow = None

        self.workspaceButtonSize = 50
        self.padding = 15 # space inside elements, e.g. distance from outer panel to track boxes
        self.verticalSpace = 10 # between vertical elements, e.g. tracks
        self.trackHeight = 80 # height of one track button, which must contain clip buttons
        self.clipWidth = 50 # width of a clip button. several of these must fit next to each other, inside of a track box
        self.clipHeight = (self.trackHeight // 2) - 5 # upper half of inside a track box is the label, lower half is the clip buttons
        self.panel = pygame_gui.elements.UIPanel(relative_rect=pygame.Rect((0, 0), (self.xres, self.yres)),
                                                 #                                                     margins={"top":10,"bottom":10,"left":10,"right":10},
                                                 object_id=ObjectID(class_id="@panel", object_id="#panel"),
                                                 manager=self.manager)

    def _maxTracks(self, y=0):
        size = self.trackHeight + self.verticalSpace
        yspace = self.yres - y - self.verticalSpace
        maxTracks = yspace // size
        return maxTracks
        
    def drawEverything(self, currentWorkspace, workspaces, lastMsg, currentTrack, tracks, override=None):
            
            
        self.panel.get_container().clear()            
        ydelta = self.drawWorkspaces(currentWorkspace, workspaces, y=self.padding)
        ydelta = self.drawMsg(lastMsg, y=ydelta, override=override)

        # scrolling stuff
        # ensure currentWindow is in good state
        k = self._maxTracks(ydelta)
        if currentWorkspace not in self.windows:
            self.windows[currentWorkspace] = (0, k)
        self.currentWindow = self.windows[currentWorkspace]
                                              

        if currentTrack is None:
            i = 0
        else:
            i = currentTrack

        while not(inWindow(i, self.windows[currentWorkspace])):
            (a, b) = self.windows[currentWorkspace]
            if b <= a:
                # window is in nonsense state. not sure how we got here, but whoever did this isn't getting to see any tracks.
                return ydelta
                
            if i >= b:
                self.windows[currentWorkspace] = moveWindow(1, self.windows[currentWorkspace])
            else: # has to be i < a
                self.windows[currentWorkspace] = moveWindow(-1, self.windows[currentWorkspace])

        return self.drawTracks(currentTrack, tracks, y=ydelta)

    def drawWorkspaces(self, currentWorkspace, workspaces, y=0):
        prev = None
        x = self.padding
        for (k, ws) in workspaces.items():
            if prev is not None:
                x += prev._rect.width + self.padding // 2

            prev = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((x, y), (self.workspaceButtonSize, self.workspaceButtonSize)),
                text="F" + str(k),
                manager=self.manager,
                starting_height=1,
                container=self.panel,
                object_id=ObjectID(class_id="@button", object_id="#workspace"))
            if k == currentWorkspace:
                prev.select()

        return y + self.workspaceButtonSize + self.verticalSpace
    
    def drawMsg(self, lastMsg, y=0, override=None):
        if override is not None:
            # override is a text input field. we can either draw it's override.value ourselves, or blit the surface
            # FIXME: this is dumb, we should just use pygame_gui text input fields. Until we do that, just use value. Damn the cursor!
            lastMsg = override.value
            
        label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((self.padding, y),(self.xres - self.padding, 25)),
            text=lastMsg,
            container=self.panel,
            object_id=ObjectID(class_id="@label", object_id="#msg"))        
        return y + label._rect.height + self.verticalSpace
    
    
    def drawTracks(self, currentTrack, tracks, y=0):
        if tracks == []:
            return y
        
        prev = None
        
        for k in range(self.currentWindow[0], self.currentWindow[1]):
            if (k < 0) or (k >= len(tracks)):
                continue

            track = tracks[k]
            if prev is not None:
                y = y + prev._rect.height + self.verticalSpace
                
            prev = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((self.padding, y), (self.xres - self.padding, self.trackHeight)),
                text=track.getDisplayName()[:100],
                manager=self.manager,
                starting_height=1,
                container=self.panel,
                object_id=ObjectID(class_id="@button", object_id="#track"))
            
            if k == currentTrack:
                prev.select()
            if track.isLocked():
                prev.disable()
                
            prevclip = None
            clipy = y + self.trackHeight // 2
            l = len(track.data)
            for i in range(0, l+1):
                if not(prevclip):
                    clipx = self.padding + (self.padding // 2)
                else:
                    clipx += self.clipWidth + (self.padding // 2)

                if i == l:
                    txt = "New Clip"
                else:
                    txt = "clip " + str(i)

                prevclip = pygame_gui.elements.UIButton(
                    relative_rect=pygame.Rect((clipx, clipy), ( self.clipWidth, self.clipHeight)),
                    text=txt,
                    manager=self.manager,
                    starting_height=2,
                    container=self.panel,
                    object_id=ObjectID(class_id="@button", object_id="#clip"))

                if track.isLocked():
                    prevclip.disable()
                if i == track.index:
                    prevclip.select()
                        
        return y + prev._rect.height
                

    def _debug(self):
        cont = self.panel.get_container().elements
        print(str(len(cont)) + " ui elements total.")
        print("current window " + str(self.currentWindow))
        for elem in cont:
            print(str(type(elem)))
            print(" - " + str(elem.get_abs_rect()))
            if "text" in elem.__dict__:
                print(" - " + elem.text)
                  
            
                
