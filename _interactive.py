# extends ViewState
from types import MethodType
import sys
import inspect

import pygame_textinput

def extend(self):
    xs = [x for x in inspect.getmembers(sys.modules[__name__], inspect.isfunction)]
    for (w, f) in xs:
        self.__dict__[w] = MethodType(lambda self: f(self), self)

def renameTrack(self):
    track = self.getCurrentTrack()
    if track is None:
        return "Sorry, no track currently selected to rename."

    def handle(w):
        if not(w):
            self.tts.speak("Please enter a new name for the track.")
            return False
        track.name = w
        self.tts.speak("Ok. Renamed track to " + w)
        self.cancelTextMode()
        return True

    self.enableTextMode(handle)
    #        self.textinput.value = track.name                    
    return "Please enter a new name for the track. Enter to confirm, escape to exit."
            
        
    
