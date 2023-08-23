#!/bin/python

# Tanto - Terminal based Video and Audio editing tool

import sys, os, threading, multiprocessing

# Disable print
def blockPrint():
    sys.stdout = open(os.devnull, 'w')

# Enable print
def enablePrint():
    sys.stdout = sys.__stdout__


blockPrint()
import pygame
from pygame.locals import *
enablePrint()

from moviepy.editor import *
from speak import Speaker
from track import Track







def getSeekPos(clip):
    if not("seekpos" in clip.__dict__):
        return 0
    return clip.seekpos

        

class ViewState(object):
    def __init__(self, tts=None, clock=None):
        self.debug = True
        self.clock = clock
        self.audiothread = None
        self.running = True
        self.tts = tts
        self.tracks = []
        self.currentTrack = None
        self.video_flag = threading.Event()
        self.audio_flag = threading.Event()

        

        testfile = "/home/marius/Videos/bghyperstream2.mkv"
        self.newTrack()
        track = self.getCurrentTrack()
        track.insertFile(testfile)

        self.smallTimeStep = 1 # in seconds
        self.largeTimeStep = 60 # in seconds

        
        self.cmds = {
            "q" : self.quit,
            "t" : self.test,
            "ENTER" : self.activate,
            "SPACE" : self.playPause,
            "a" : lambda: self.shiftFocus((-1,0)),
            "s" : lambda: self.shiftFocus((0, 1)),
            "w" : lambda: self.shiftFocus((0, -1)),
            "d" : lambda: self.shiftFocus((1,0)),
            "n" : self.newTrack,
            "h" : self.whereAmI,
            "f" : lambda: self.seekRelative(self.smallTimeStep),
            "b" : lambda: self.seekRelative((-1)*self.smallTimeStep),
            "F" : lambda: self.seekRelative(self.largeTimeStep),
            "B" : lambda: self.seekRelative((-1)*self.largeTimeStep)}

        for n in list(range(0,10)):
            self.cmds[str(n)] = lambda n=n: self.seekPercentage(n*10)


    def quit(self):
        self.running = False
        return "bye"


    def test(self):
        clip = VideoFileClip("/home/marius/Videos/bghyperstream2.mkv")
        sub = clip.subclip(10000, 10100)
        sub.preview()

    def activate(self):
        return ""

    def shiftFocus(self, pos):
        (x, y) = pos
        if self.currentTrack is None:
            return "No tracks. Please create a new track by hitting n."

        if y != 0:
            new = self.currentTrack+y
            new = max(0, new)
            self.currentTrack = min(len(self.tracks)-1, new)
            print(str(self.currentTrack))


        track = self.getCurrentTrack()
        if not(track):
            return ""

        if x > 0:
            track.right()
        elif x < 0:
            track.left()

        return ""


    def getCurrentTrack(self):
        if self.currentTrack is None:
            return None

        return self.tracks[self.currentTrack]

    def whereAmI(self):
        w = "track " + str(self.currentTrack)
        track = self.getCurrentTrack()
        if track is None:
            return "Please create at least 1 track."

        w += "clip " + str(track.index)
        return w

    def newTrack(self):
        self.tracks.append(Track())
        self.currentTrack = len(self.tracks)-1
        return "Ok"


    def getCurrentClip(self):
        track = self.getCurrentTrack()
        if track:
            return track.get()
        return None



    def seekPercentage(self, p):
        clip = self.getCurrentClip()
        if clip is None:
            return "No clip!"

        t = clip.duration * (p/100.0)
        return self.seek(t)

    def seekRelative(self, tstep):
        clip = self.getCurrentClip()
        if clip is None:
            return "No clip!"

        t = getSeekPos(clip)
        return self.seek(t+tstep) # FIXME: this won't work for non-second time signatures

    def seek(self, t):
        clip = self.getCurrentClip()
        if clip is None:
            return "No clip!"

        clip.seekpos = t
        if self.isPlaying():
            self.playPause()
            self.playPause()
            
        return ""
        

    def isPlaying(self):
        return self.video_flag.is_set()

    def playPause(self):
        # check if we're currently playing
        if self.video_flag.is_set():
            self.video_flag.clear()
            return ""
        

        clip = self.getCurrentClip()
        if not(clip):
            return "Track has no clip to play."

        clip = clip.subclip(getSeekPos(clip))
        fps=15
        audio_fps=22050
        audio_buffersize=3000
        audio_nbytes=2


        audiothread = threading.Thread(
            target=clip.audio.preview,
            args=(audio_fps, audio_buffersize, audio_nbytes, self.audio_flag, self.video_flag),
        )
        audiothread.start()
        self.video_flag.set()
        
        
        
        return ""
    
        
            
        
def main(argv):
    (xres, yres) = (1024, 768)

    buffer = 2 * 2048
    freq=48000
    pygame.mixer.pre_init(frequency=freq, buffer=buffer)
    pygame.init()
    pygame.mixer.init(freq, -16, 2, buffer)    
    screen = pygame.display.set_mode((xres,yres))
    st = ViewState(tts=Speaker(), clock= pygame.time.Clock())
    
    while st.running:
        time_delta = st.clock.tick(60)/1000.0

        for event in pygame.event.get():
            if event.type == KEYDOWN:
                if event.key == 13: #enter
                    f = st.cmds.get("ENTER", False)
                elif event.key == K_SPACE:
                    f = st.cmds.get("SPACE", False)                    
                elif event.key == 9: # tab
                    f = st.cmds.get("TAB", False)
                else:
                    f = st.cmds.get(event.unicode, False)
                if f:
                    msg = f()
                    if msg:
                        st.tts.speak(msg)

            if event.type == QUIT:
                st.quit()


        screen.fill(pygame.color.THECOLORS["black"])
        pygame.display.update()
        

    # cleanup
    pygame.quit()
    sys.exit()




if __name__ == "__main__":        
    main(sys.argv)


    

