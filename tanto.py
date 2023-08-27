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
import pygame_textinput
import pygame
from pygame.locals import *
enablePrint()

from moviepy.editor import *
from speak import Speaker
from track import Track
from tanto_utility import *



class ViewState(object):
    def __init__(self, tts=None, projectdir="./", textinput=None):
        self.debug = True
        self.textinput = textinput
        self.projectdir = projectdir
        self.running = True
        self.tts = tts
        self.graveyard = Track(name="graveyard", locked=True)
        self.tracks = [self.graveyard]
        self.head = None
        self.currentTrack = None
        self.video_flag = threading.Event()
        self.audio_flag = threading.Event()

        self.quietFactor = 0.2
        self.smallTimeStep = 1 # in seconds
        self.largeTimeStep = 60 # in seconds
        self.volumeStep = 0.1

        if self.projectdir:
            self.loadDir(self.projectdir)


            self.textmode = False
            self.defaultTextHandler = lambda w: True
            self.handleText = self.defaultTextHandler
        self.cmds = {
            "q" : self.quit,
            "Q" : self.save,
            "ENTER" : self.setMark,
            "BACKSPACE" : self.jumpToMark,
            "e" : self.setMarkEnd,
            '"' : self.createVoiceClip,
            "!" : self.createSilenceClip,
            "§" : self.createVoiceOver,
            "$" : lambda: self.createVoiceOver(file=True),
            ";" : self.renameTrack,
            "=" : self.setVolume,
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
            "CTRL+r" : self.removeTrack,
            "CTRL+l" : self.toggleLock,
            "<" : self.minFocus,
            ">" : self.maxFocus,
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
            newTrack = self.makeSideTrack(track)

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
        if end >= clip.duration:
            afterclip = clip
        else:
            afterclip = clip.subclip(end)
        return (preclip, sclip, afterclip)


    def getCurrentSubclip(self):
        sclip = self.getCurrentTrisection()[1]
        if sclip is None:
            return None
        
        # more intuitive to have mark and seekpos reset on new clip
        setMark(sclip, 0)
        setSeekPos(sclip, 0)
        return sclip
        


    def toggleLock(self):
        track = self.getCurrentTrack()
        if track is None:
            return "Cannot lock or unlock: No track selected."

        if track.name == "graveyard":
            if track.isLocked():
                return "Cannot unlock graveyard. Sorry."
            track.lock()
            return "Abandon all hope, ye who enter the graveyard, for it is locked!"


        if track.isLocked():
            track.unlock()
            return "Track unlocked."
        track.lock()
        return "Track locked."
       
    def removeClip(self):
        track = self.getCurrentTrack()
        if track is None:
            return "No track to remove clip from."


        if track.isLocked():
            return "Cannot remove clip: Owning track is locked."
        
        if track.empty():
            return "Can't remove clip: No clips in track."

        clip = track.get()
        track.remove()
        self.graveyard.insertClip(clip)
        return "Ok. Clip moved to graveyard."
        

    def removeTrack(self):
        track = self.getCurrentTrack()
        if track is None:
            return "Cannot remove track: No current track selected."

        if track.isLocked():
            return "Cannot remove track: Track is locked."

        n = 0
        name = track.getName()
        track.rewind()
        while not(track.empty()):
            n += 1
            self.removeClip()

        del self.tracks[self.currentTrack]
        self.shiftFocus((0, -1))
        return "Ok. Removed track " + name + ". Moved " + str(n) + "clips to graveyard."

            
            
        
        return "remove track"
    
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
        newTrack.name = self.makeSubTrackName(track)
        return newTrack


    def makeSideTrack(self, track):
        newTrack = track.clone()
        newTrack.name = self.makeSideTrackName(track)
        return newTrack
    

    def makeSubTrackName(self, track):
        name = subTrackName(track.getName())
        allNames = list(map(lambda t: t.getName(), self.tracks))
        while True: # we *will* name this
            if not(name in allNames):
                return name
            name = sideTrackName(name)

    def makeSideTrackName(self, track):
        name = sideTrackName(track.getName())
        allNames = list(map(lambda t: t.getName(), self.tracks))
        while True:
            if not(name in allNames):
                return name
            name = sideTrackName(name)
                    
                


        

    
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

        destinationTrack.name = self.makeSubTrackName(sourceTrack)
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
            self.setCurrentClip(clip.multiply_volume(factor))
            return "Ok. Changed volume by " + str(step)

        (preclip, sclip, afterclip) = self.getCurrentTrisection()
        sclip = sclip.multiply_volume(factor)
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
            
        
    
    def setVolume(self):
        clip = self.getCurrentClip()
        if clip is None:
            return "Sorry, must be on a clip to set its volume."


        def cont(p):
            if p < 0.0:
                self.tts.speak("Can't set volume to negative number. Please specify a positive decimal number, like 0.2 or 3.1")
                return False

            self.setCurrentClip(clip.multiply_volume(p))
            self.cancelTextMode()
            self.tts.speak("Ok. scaled volume to " + str(p) + " times its original value.")
            return True
        
        self.enableTextMode(self.makeFloatHandler(cont))
        return "Please specify a volume multiplier as a decimal. 1.0 means no change, 0.0 is silence, 1.2 increases volume by 20%."


    def makeFloatHandler(self, cont):
        def h(w):
            if not(isFloat(w)):
                self.tts.speak("Sorry, invalid input. Please specify a valid number.")
                return False

            try:
                n = float(w)
            except:
                self.tts.speak("Sorry, invalid input. Please specify the silence duration in seconds.")
                return False            

            return cont(n)
        return h


    def createVoiceOver(self, file=False):
        # enter a text and it is spoken and mixed into the current clip, at the mark position, while quieting the clip it is mixed into
        # file = true means you enter a name of a text file instead
        track = self.getCurrentTrack()
        if track is None:
            return "Sorry, please select a track or create one."
        
        clip = self.getCurrentClip()
        if clip is None:
            return "Sorry, no clip!"

        if isAudioClip(clip):
            return "Sorry, direct voice over for audio clips is currently not supported."


        mark = getMark(clip)
        
        def handle(w):
            if not(w):
                if file:
                    st.tts.speak("Please enter a file name.")
                else:
                    self.tts.speak("Please enter some text for the voice over.")
                return False

            if file:
                try:
                    v = open(w, "r").read()
                except:
                    st.tts.speak("Error opening file. Please specify a valid text file to crate the voice over from.")
                    return False
                w = v
                
                

            voice = makeVoiceClip(w)
            duration = voice.duration
            if duration >= (clip.duration - mark):
                self.tts.speak("Message is too long for the clip!")
                return False
            begin = resetClipPositions(clip.subclip(0, mark))
            middle = resetClipPositions(clip.subclip(mark, mark+duration))
            end = resetClipPositions(clip.subclip(mark+duration, clip.end))
            # FIXME: this currently will crash on pure audio clips, but voice over is mostly used for video anyway
            middle = middle.multiply_volume(self.quietFactor)
            middle.audio = makeCompositeAudioClip([middle.audio, voice])
            tmp = Track()
            tmp.insertClip(begin)
            tmp.insertClip(middle)
            tmp.insertClip(end)
            self.newTrack()
            nt = self.getCurrentTrack()
            nt.name = self.makeSubTrackName(track)
            nt.insertClip(tmp.concatenate())

            self.tts.speak("Ok. Inserted voice over at mark and copied to new track " + nt.getName() + ".")
            self.cancelTextMode()
            return True

        self.enableTextMode(handle)
        if file:
            return "Please enter the filename of a textfile to create the voice over from."
        return "Please enter a text for the voice over."

    def createSilenceClip(self):
        if self.head:
            track = self.head
        else:
            self.newTrack()
            track = self.getCurrentTrack()

        def cont(n):
            if n <= 0:
                self.tts.speak("Please enter a positive, non-zero value.")
                return False

            track.insertClip(makeSilenceClip(n))
            self.tts.speak("Ok. Created " + str(n) + " seconds of silence at head position.")
            self.cancelTextMode()
            return True

        self.enableTextMode(self.makeFloatHandler(cont))
        return "Please enter the duration of silence in seconds. Enter to confirm, escape to cancel."
            
    def createVoiceClip(self):
        # get text input, then, make a voice over wav file, and add it to the current head position
        if self.head:
            track = self.head
        else:
            self.newTrack()
            track = self.getCurrentTrack()

        def handleVoiceMessage(w):
            clip = makeVoiceClip(w)
            track.insertClip(clip)
            self.cancelTextMode()
            return True #delete text

        self.enableTextMode(handleVoiceMessage)
        return "Enter the message to be spoken. Enter to submit, escape to cancel."


        
    def isTextMode(self):
        return self.textmode

    def cancelTextMode(self):
        self.handleText = self.defaultTextHandler
        self.textinput.value = ""
        self.textmode = False

    def enableTextMode(self, handler):
        self.handleText = handler
        self.textinput.value = ""
        self.textmode = True
    
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


    def minFocus(self):
        if self.tracks == []:
            return "No tracks. Please create a new track by hitting n."

        self.currentTrack = 0
        track = self.getCurrentTrack()
        return track.getDisplayName()

    def maxFocus(self):
        if self.tracks == []:
            return "No tracks. Please create a new track by hitting n."

        self.currentTrack = len(self.tracks)-1
        track = self.getCurrentTrack()
        return track.getDisplayName()
    
        
        
        
    def shiftFocus(self, pos):
        (x, y) = pos
        if self.currentTrack is None:
            return "No tracks. Please create a new track by hitting n."

        if y != 0:
            new = self.currentTrack+y
            new = max(0, new)
            self.currentTrack = min(len(self.tracks)-1, new)
            return  self.tracks[self.currentTrack].getDisplayName()


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
    
        
            


def getKeyRepresentation(event):
    # we like keys as simple strings with all modifiers like so "CTRL+ALT+ENTER" etc.
    w = ""
    d = {K_RETURN : "ENTER", K_SPACE : "SPACE", K_TAB : "TAB", K_BACKSPACE : "BACKSPACE"}
    keystring = d.get(event.key, event.unicode)

    
    keys = pygame.key.get_pressed()
    if keys[K_LCTRL] or keys[K_RCTRL]:
        w += "CTRL+"
        keystring = pygame.key.name(event.key) #unicode representation is messed up when some modifiers are present

    if keys[K_LALT] or keys[K_RALT]:
        w += "ALT+"
        keystring = pygame.key.name(event.key)

    # FIXME: do shift?
    
    return w + keystring
    
def main(argv):
    (xres, yres) = (1024, 768)

    buffer = 2 * 2048
    freq=48000
    pygame.mixer.pre_init(frequency=freq, buffer=buffer)
    pygame.init()
    pygame.mixer.init(freq, -16, 2, buffer)    
    screen = pygame.display.set_mode((xres,yres))
    clock = pygame.time.Clock()
    textinput = pygame_textinput.TextInputVisualizer()    
    projectdir = None    
    if len(argv) == 2:
        if os.path.isdir(argv[1]):
            projectdir = argv[1]

    st = ViewState(tts=Speaker(), projectdir=projectdir, textinput=textinput)
    
    while st.running:
        time_delta = clock.tick(60)/1000.0
        events = pygame.event.get()
        textinput.update(events)
        screen.blit(textinput.surface, (10, yres-20))        
        for event in events:
            if event.type == KEYDOWN:
                if st.isTextMode():
                    st.tts.speak(textinput.value)
                    if event.key == 13: # enter
                        if pygame.key.get_pressed()[K_LCTRL]:
                            # control enter makes a newline
                            textinput.value += "\n"
                            textinput.manager.cursor_pos += 1
                            continue
                            
                        deleteText = st.handleText(textinput.value)
                        if deleteText:
                            textinput.value = ""
                    elif event.key == K_ESCAPE:
                        st.cancelTextMode()
                    continue


                f = st.cmds.get(getKeyRepresentation(event), False)
                if f:
                    msg = f()
                    if msg:
                        st.tts.speak(msg)
                        if not(st.isTextMode()):
                            textinput.value = msg

            if event.type == QUIT:
                st.quit()


        screen.fill(pygame.color.THECOLORS["black"])
        pygame.display.update()
        

    # cleanup
    pygame.quit()
    sys.exit()




if __name__ == "__main__":        
    main(sys.argv)


    


