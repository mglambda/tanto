#!/bin/python

# Tanto - Terminal based Video and Audio editing tool

import sys, os, glob, threading, multiprocessing, time

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
from tanto_utility import *



class ViewState(object):
    def __init__(self, tts=None, projectdir="./"):
        self.debug = True
        self.projectdir = projectdir
        self.running = True
        self.tts = tts
        self.graveyard = Track(name="graveyard")
        self.tracks = [self.graveyard]
        self.head = None
        self.currentTrack = None
        self.video_flag = threading.Event()
        self.audio_flag = threading.Event()

        

#        testfile = "/home/marius/Videos/bghyperstream2.mkv"

        self.smallTimeStep = 1 # in seconds
        self.largeTimeStep = 60 # in seconds
        self.volumeStep = 0.1

        if self.projectdir:
            self.loadDir(self.projectdir)
        
        self.cmds = {
            "q" : self.quit,
            "Q" : self.save,
            "ENTER" : self.setMark,
            "BACKSPACE" : self.jumpToMark,
            "e" : self.setMarkEnd,
            "SPACE" : self.playPause,
            "x" : self.setHead,
            "X" : self.whereIsHead,
            "v" : self.bisect,
            "V" : lambda: self.bisect(inPlace=True),
            "c" : self.copyToHead,
            "m" : self.mergeTrack,
            "M" : lambda: self.mergeTrack(fade=True),
            "p" : self.mixAudio,
            "P" : lambda: self.mixAudio(inPlace=True),
            "+" : lambda: self.changeVolume(self.volumeStep),
            "-" : lambda: self.changeVolume((-1) * self.volumeStep),
            "S" : self.saveClip,
            "_" : self.saveTrack,
            "r" : self.removeClip,
            "a" : lambda: self.shiftFocus((-1,0)),
            "s" : lambda: self.shiftFocus((0, 1)),
            "w" : lambda: self.shiftFocus((0, -1)),
            "d" : lambda: self.shiftFocus((1,0)),
            "n" : self.newTrack,
            "h" : self.whereAmI,
            "t" : self.whereMark,
            "^" : lambda: self.stepFactor(0.1),
            "´" : lambda: self.stepFactor(10),
            "f" : lambda: self.seekRelative(self.smallTimeStep),
            "b" : lambda: self.seekRelative((-1)*self.smallTimeStep),
            "F" : lambda: self.seekRelative(self.largeTimeStep),
            "B" : lambda: self.seekRelative((-1)*self.largeTimeStep)}

        for n in list(range(0,10)):
            self.cmds[str(n)] = lambda n=n: self.seekPercentage(n*10)



    def loadDir(self, dir):
        for file in glob.glob(dir + "/*"):
            print(file)
            if os.path.isdir(file):
                self.tracks.append(Track.fromDir(file))
            else:
                self.loadFile(file)
                
            
    def loadFile(self, file):
        name = trackNameFromFile(file, "track " + str(len(self.tracks)))            
        self.newTrack(name=name, audioOnly=isAudioFile(file))
        track = self.getCurrentTrack()
        track.insertFile(file)
        track.left()



        
    def save(self, file=None):
        pass
        
    def quit(self):
        if self.isPlaying():
            self.playPause()
            
        self.running = False
        return "bye"



    def setMark(self, pos=None):
        clip = self.getCurrentClip()
        if clip is None:
            return "No clip!"
        if not(pos):
            pos = getSeekPos(clip)
        setMark(clip, pos)
        return "Mark set at " + toTimecode(getMark(clip))

    def setMarkEnd(self):
        clip = self.getCurrentClip()
        if clip is None:
            return "No clip!"
        return self.setMark(pos=clip.end)

    def whereMark(self):
        clip = self.getCurrentClip()
        if clip is None:
            return "No clip!"

        mark= getMark(clip)
        seek = getSeekPos(clip)
        return "seek at " + toTimecode(seek) + ", mark at " + toTimecode(mark)
        
    
    def jumpToMark(self):
        clip = self.getCurrentClip()
        if clip is None:
            return "No clip!"

        mark = getMark(clip)
        return self.seek(mark)


    def bisect(self, inPlace=False):
        # cuts current clip at its mark, and creates a new track with 2 clips instead of one. Can also be called to cut-inplace, modfying the current track
        clip = self.getCurrentClip()
        if clip is None:
            return "Cannot cut here: No clip!"

        mark = getMark(clip)
        if mark == 0 or mark >= clip.end:
            return "Nonsense mark position, nothing cut."

        a = clip.subclip(0, mark)
        b = clip.subclip(mark)
        resetClipPositions(a)
        resetClipPositions(b)
        
        track = self.getCurrentTrack()
        if inPlace:
            newTrack = track
        else:
            newTrack = self.makeCloneTrack(track)

        newTrack.insertClip(a)
        newTrack.insertClip(b)
        newTrack.remove()
        if not(inPlace):
            self.appendTrack(newTrack)
        w = "Ok. cut clip onto "
        if not(inPlace):
            w += "new track "
        return w + newTrack.getName()
            
                
            
            
            
        
    def setHead(self):
        track = self.getCurrentTrack()
        if track is None:
            return "No track selected."
        self.head = track
        return "Head is now at " + self.strHead()


    def strHead(self):
        if self.head is None:
            return "none"

        w = self.head.getName() + " at " + self.head.strIndex()
        clip = self.head.get()
        if clip is None:
            return w

        if getMark(clip) == 0:
            return w
        return w + " with mark at " + toTimecode(getMark(clip))

        

    
    def getHeadClip(self):
        if self.head is None:
            return None

        return self.head.get()
        
        
    

    def getCurrentTrisection(self):
        # returns subclip between seekpos and mark, as well as preclip and afterclip
        clip = self.getCurrentClip()
        if clip is None:
            return (None, None, None)

        mark = getMark(clip)
        pos = getSeekPos(clip)
        begin = min(mark, pos)
        end = max(mark,pos)
        preclip = clip.subclip(0, begin)
        sclip = clip.subclip(begin, end)
        afterclip = clip.subclip(end)
        return (preclip, sclip, afterclip)


    def getCurrentSubclip(self):
        sclip = self.getCurrentTrisection()[1]
        # more intuitive to have mark and seekpos reset on new clip
        setMark(sclip, 0)
        setSeekPos(sclip, 0)
        return sclip
        


    def removeClip(self):
        track = self.getCurrentTrack()
        if track is None:
            return "No track to remove clip from."

        if track.empty():
            return "Can't remove clip: No clips in track."

        clip = track.get()
        track.remove()
        self.graveyard.insertClip(clip)
        return "Ok. Clip moved to graveyard."
        

    def mixAudio(self, inPlace=False):
        # get the audio from subclip between mark and seekpos, and mix it into the audio of the clip at HEAD
        # if the mixed-in audio clip is longer than clip at head, it is cropped
        source = self.getCurrentSubclip()
        if source is None:
            return "No clip to mix audio from."

        track = self.head
        if track is None:
            return "Cannot mix audio. Head is not set."

        target = track.get()
        if target is None:
            return "No clip to mix audio into."

        if source == target:
            return "Mixing audio of a clip into itself is not suported yet."
        
        if isAudioClip(source):
            audioSource = source
        else:
            audioSource = source.audio

        if isAudioClip(target):
            audioTarget = target
        else:
            audioTarget = target.audio

        newAudio = makeCompositeAudioClip([audioTarget, audioSource], offset=getMark(target))
        if inPlace:
            newTrack = track
        else:
            newTrack = self.makeCloneTrack(track)


        newTarget = newTrack.get()
        if isAudioClip(newTarget):
            newTrack.data[newTrack.index] = newAudio
        else:
            newTarget.audio = newAudio

        if not(inPlace):
            self.appendTrack(newTrack)
        w = "Ok. Mixed in audio track onto "
        if not(inPlace):
            w+= "new track "
        return w + newTrack.getName()
        
                

       

    def makeCloneTrack(self, track):
        newTrack = track.clone()
        newTrack.name = self.makeCloneTrackName(track)
        return newTrack


    def makeCloneTrackName(self, track):
        return str(len(self.tracks)) + " - " + track.name
    
    def mergeTrack(self, fade=False):
        sourceTrack = self.getCurrentTrack()
        if sourceTrack is None:
            return "No track."

        if sourceTrack.empty():
            return "Track has no clips to merge."

        if not(sourceTrack.isMergable()):
            return "Tracks must contain only video clips, or only audio clips to be merged.This track seems to contain both."

        self.newTrack()
        destinationTrack = self.getCurrentTrack()
        if destinationTrack is None:
            return "Something went wrong. Couldn't create new track. Aborting merge."

        destinationTrack.name = self.makeCloneTrackName(sourceTrack)
        destinationTrack.insertClip(sourceTrack.concatenate(fade=fade))
        return "Ok. Merged clips onto " + destinationTrack.getName()

        
        
        

    def saveTrack(self):
        track = self.getCurrentTrack()
        if track is None:
            return "Cannot save. No track to save."
        
        track.save(self.projectdir)
        
    
    def saveClip(self):
        clip = self.getCurrentClip()
        if clip is None:
            return "No clip to save."

        track = self.getCurrentTrack()
        if track:
            name =  track.getName() + "-" + track.strIndex()
            name = name.replace(" ", "-")
        else:
            name = "unknown_clip"

        extension = ".mkv"
        clip.write_videofile(name+extension, codec="libx264")
        return "Ok. Wrote file " + name+extension
            


        
    

    def changeVolume(self, step):
        factor = 1.0 + step

        clip = self.getCurrentClip()
        if clip is None:
            return "Cannot change volume: no clip."

        mark = getMark(clip)
        if mark == 0:
            self.setCurrentClip(clip.volumex(factor))
            return "Ok. Changed volume by " + str(step)

        (preclip, sclip, afterclip) = self.getCurrentTrisection()
        sclip = sclip.volumex(factor)
        tmp = Track()
        tmp.insertClip(preclip)
        tmp.insertClip(sclip)
        tmp.insertClip(afterclip)
        newClip = tmp.concatenate()
        if newClip is None:
            return "Oops. Couldn't change volume due to unknown error."
        setSeekPos(newClip, getSeekPos(clip))
        setMark(newClip, mark)
        #FIXME: this sometimes introduces an audioble clicking noise or other artefacts. not sure why
        self.setCurrentClip(newClip)
        return "Ok, changed volume of clip section by " + str(step)
        

        

        


        
            
        
        
    
    def copyToHead(self):
        clip = self.getCurrentSubclip()
        if clip is None:
            return "No clip to copy!"
        
        track = self.head
        if track is None:
            return "Head is not set!"

        track.insertClip(clip)
        return "Copied clip to " + track.getName()

    def whereIsHead(self):
        if self.head is None:
            return "Head is not set."


        return "Head is set to " + self.strHead()

    def test(self):
        clip = VideoFileClip("/home/marius/Videos/bghyperstream2.mkv")
        sub = clip.subclip(10000, 10100)
        sub.preview()

    def activate(self):
        return ""


    def stepFactor(self, factor):
        self.smallTimeStep *= factor
        self.largeTimeStep *= factor
        return "timesteps are " + str(self.smallTimeStep) + " and " + str(self.largeTimeStep)
    
    def shiftFocus(self, pos):
        (x, y) = pos
        if self.currentTrack is None:
            return "No tracks. Please create a new track by hitting n."

        if y != 0:
            new = self.currentTrack+y
            new = max(0, new)
            self.currentTrack = min(len(self.tracks)-1, new)
            return  self.tracks[self.currentTrack].getName()


        track = self.getCurrentTrack()
        if track is None:
            return ""

        if x > 0:
            track.right()
        elif x < 0:
            track.left()
        return track.strIndex()


    def getCurrentTrack(self):
        if self.currentTrack is None:
            return None

        return self.tracks[self.currentTrack]

    def whereAmI(self):
        track = self.getCurrentTrack()
        if track is None:
            return "Please create at least 1 track."
        w = track.getName()
        w += " at " + track.strIndex()
        
        clip = self.getCurrentClip()
        if clip is None:
            return w
        w += " at position " + toTimecode(getSeekPos(clip))
        if isAudioClip(clip):
            print(str(type(clip)))
            print(str(type(clip).__mro__))
            w += " *audio*"
        if isVideoClip(clip):
            w += " *video*"
            
        return w

    def newTrack(self, name=None, audioOnly=False):
        if name is None:
            name = "track " + str(len(self.tracks))
            
        self.appendTrack(Track(name=name, audioOnly=audioOnly))
        self.currentTrack = len(self.tracks)-1
        return "Ok"


    def appendTrack(self, track):
        self.tracks.append(track)
        

    def getCurrentClip(self):
        track = self.getCurrentTrack()
        if track:
            return track.get()
        return None

    def setCurrentClip(self, clip):
        track = self.getCurrentTrack()
        if track is None:
            return

        if track.empty():
            return

        if track.get() is None:
            return

        track.data[track.index] = clip
        



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

        if clip.duration > t:
            clip.seekpos = t
        else:
            clip.seekpos = clip.end
            
        if self.isPlaying():
            self.playPause()
            time.sleep(0.1)
            self.playPause()
            return "" # don't interrupt playback
        return "seek to " + toTimecode(t)

        

    def isPlaying(self):
        return self.video_flag.is_set()

    def playPause(self):
        # check if we're currently playing
        if self.video_flag.is_set():
            self.video_flag.clear()
            self.video_flag = threading.Event()
            self.audio_flag = threading.Event()
            return ""
        

        clip = self.getCurrentClip()
        if not(clip):
            return "No clip to play!"


        if getSeekPos(clip) >= clip.duration:
            return "End of clip."
        
        clip = clip.subclip(getSeekPos(clip))
        fps=15
        audio_fps=22050
        audio_buffersize=3000
        audio_nbytes=2
        if isVideoClip(clip):
            clip = clip.audio
            
        audiothread = threading.Thread(
            target=clip.preview, # important: this is clip.audio.preview for normal video clips
            args=(audio_fps, audio_buffersize, audio_nbytes, self.audio_flag, self.video_flag),
        )
        audiothread.start()
        self.video_flag.set()
        self.audio_flag.wait()
        
        
        return ""
    
        
            
        
def main(argv):
    (xres, yres) = (1024, 768)

    buffer = 2 * 2048
    freq=48000
    pygame.mixer.pre_init(frequency=freq, buffer=buffer)
    pygame.init()
    pygame.mixer.init(freq, -16, 2, buffer)    
    screen = pygame.display.set_mode((xres,yres))
    clock = pygame.time.Clock()
    projectdir = None    
    if len(argv) == 2:
        if os.path.isdir(argv[1]):
            projectdir = argv[1]

    st = ViewState(tts=Speaker(), projectdir=projectdir)
    
    while st.running:
        time_delta = clock.tick(60)/1000.0

        for event in pygame.event.get():
            if event.type == KEYDOWN:
                if event.key == 13: #enter
                    f = st.cmds.get("ENTER", False)
                elif event.key == K_SPACE:
                    f = st.cmds.get("SPACE", False)
                elif event.key == K_BACKSPACE:
                    f = st.cmds.get("BACKSPACE", False)                                        
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


    


