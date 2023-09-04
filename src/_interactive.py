# extends ViewState

import sys, os, glob, threading, multiprocessing, time
from types import MethodType
from track import *
from tanto_utility import *
import inspect
import pygame_textinput

def extend(self):
    xs = [x for x in inspect.getmembers(sys.modules[__name__], inspect.isfunction)]
    for (w, f) in xs:
        self.__dict__[w] = MethodType(f, self)

#########################################################################################################################################################################################################################################
# Below are all functions that will be imported by ViewState as methods, so the self parameter refers to a ViewState object.                                                                                                            #
# These functions are (by convention) all considered 'interactive'. This means they are intended to be bound to a key and invoked directly by the program's main loop. See _keybindings.py for examples of how to bind these functions. #
# Interactive functions have three constraints:                                                                                                                                                                                         #
#   (1) They must be objects that are callable with zero parameters.                                                                                                                                                                    #
#   (2) They must return a string, which will be read out by the TTS engine, and also displayed at the top of the program. The intended purpose is to give the user instant feed back on pressing a button.                             #
#   (3) They must not be blocking, as this would leave the entire program unresponsive, including the UI.                                                                                                                               #
# Apart from that, anything can be an interactive function, and interactive functions can and are used outside of the interactive context.                                                                                              #
#########################################################################################################################################################################################################################################

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

def keyInfo(self):
    self._tmpcmds = self.cmds.copy()
    def mkHelp(key):
        def f():
            self.cmds = self._tmpcmds
            return self.help.get(key, (None, "Key not bound."))[1]
        return f
    for (k, v) in self.cmds.items():
        self.cmds[k] = mkHelp(k)

    return "Press any key or key combo to hear its description."
   

def printDebug(self):
    if not(self.debug ):
        return ""

    self.ui._debug()
    return "Printed debug information to standard output."



def quit(self):
    if self.isPlaying():
        self.playPause()

    self.storeTrackVars()
    self.running = False
    return "bye"




def saveMark(self):
    clip = self.getCurrentClip()
    if clip is None:
        return "Cannot save mark: No clip!"

    self.saveMark = getMark(clip)
    return "Saved mark " + showMark(mark)

def pasteMark(self):
    track = self.getCurrentTrack()
    clip = self.getCurrentClip()
    if clip is None:
        return "Need a clip to paste mark onto."

    mark = self.saveMark
    if mark is None:
        return "No mark to paste."

    setMark(clip, mark)
    return "Set mark to " + showMark(mark)






def interactiveSetMark(self, pos=None):
    clip = self.getCurrentClip()
    if clip is None:
        return "No clip!"
    if not(pos):
        pos = getSeekPos(clip)
    setMark(clip, pos)
    return "Mark set at " + toTimecode(getMark(clip))


def setMarkPercentage(self, p):
    clip = self.getCurrentClip()
    if clip is None:
        return "No clip!"

    t = clip.duration * (p/100.0)
    return self.interactiveSetMark(t)


def setMarkEnd(self):
    clip = self.getCurrentClip()
    if clip is None:
        return "No clip!"
    return self.interactiveSetMark(pos=clip.end)

def setMarkStart(self):
    clip = self.getCurrentClip()
    if clip is None:
        return "No clip!"
    return self.interactiveSetMark(clip.start)

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


def setHeadOffset(self):
    # sets the offset of track at head to current clip's mark
    # this is used mostly to neatly position linked tracks for merging
    clip = self.getCurrentClip()
    if clip is None:
        return "Need a clip to set offset!"

    if self.head is None:
        return "Cannot set offset: Head is not pointing at any track."

    mark = getMark(clip)
    self.head.setOffset(mark)
    return "offset " + showMark(mark) + " for " + self.head.getName()




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






def createLinkTrack(self):
    clip = self.getCurrentClip()
    if clip is None:
        return "Need a clip to link the track to."

    track = self.getCurrentTrack()
    if track is None:
        return "Something went wrong (no track??)"

    mark = getMark(clip)
    nt = Track(name=self.makeLinkTrackName(track, track.index), parent=(track.name, track.index), offset=mark, workspacePreference=self.currentWorkspace)
    self.tracks.insert(self.currentTrack+1, nt)
    self.shiftFocus((0, 1))
    self.head = nt
    return "Created linked track " + nt.getName() + " and pointed head at it."


def setHead(self):
    track = self.getCurrentTrack()
    if track is None:
        return "No track selected."
    self.head = track
    return "Head is now at " + self.strHead()

def toggleHeadOverride(self):
    self.headOverride = not(self.headOverride)
    return self.specialOverrideMsg



def switchHead(self):
    # switches position with head
    # it should hod that "Tab TAB" is an identity, i.e. you end up where you started
    if self.head is None:
        return "Head is not set."

    prev = self.getCurrentTrack()
    res = self.findTrackIndices(self.head)
    if res is None:
        return "Cannot find track to switch to."

    (headIndex, headWorkspace) = res
    self.currentTrack = headIndex
    self.currentWorkspace = headWorkspace
    self.head = prev
    if self.head.index is not None:
        w = "to " + self.head.strIndex() + " in"
    else:
        w = ""

    return "Tabbed to head at " + w + " " + self.head.getName()








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


def cutClip(self, copy=False):
    verb = "cut"
    if copy:
        verb = "copy"

    track = self.getCurrentTrack()
    if track is None:
        return "Cannot " + verb + ": No track!"

    if (copy == False) and (track.isLocked()):
        return "Cannot " + verb + " clip because track is locked."

    clip = self.getCurrentClip()
    if clip is None:
        return "Cannot " + verb + " clip: No clip!"

    if getMark(clip) == getSeekPos(clip):
        return "Refusing to " + verb + " due to nonsense mark position."

    (before, middle, after) = self.getCurrentTrisection()

    self._putClipboard(middle)
    if copy:
        return "Copied clip with duration " + showMark(middle.duration)

    # leave nothing behind if entire clip is cut
    # happens in two cases 1) pos=0, mark=end, 2) pos=0, mark=0, i.e. clip hasn't been touched
    if ((before.duration == 0) and (after.duration == 0)) or ((getMark(clip) == 0) and (getSeekPos(clip) == 0)):
        track.remove()

        return "Cut clip."

    if isAudioClip(clip):
        newClip = CompositeAudioClip([before, after.with_start(before.end)])
    else:
        newClip = CompositeVideoClip([before, after.with_start(before.end)])

    track.remove()
    track.insertClip(newClip)
    return "Cut " + showMark(middle.duration) + " from clip."


def paste(self):
    clip = self._getClipboard()
    if clip is None:
        return "Clipboard is empty."

    track = self.getCurrentTrack()
    if track is None:
        return "No track to paste into! Maybe create a new one?"

    track.insertClip(resetClipPositions(clip))
    return "Pasted clip with " + showMark(clip.duration) + " into " + track.getName()







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

def setParentAudioFactor(self, factor=None):
    track = self.getCurrentTrack()
    if track is None:
        return "Cannot set factor for parent audio: No track."

    if not(track.hasParent()):
        return "Cannot set parent audio: Track is not linked."

    if not(factor is None):
        track.setParentAudioFactor(factor)
        return "Set parent audio factor to " + str(factor) + " for the duration of track " + track.getName()

    def cont(p):
        if p < 0.0:
            self.tts.speak("Can't set volume to negative number. Please specify a positive decimal number, like 0.2 or 3.1")
            return False

        track = self.getCurrentTrack()
        if track is None:
            self.tts.speak("Something went wrong. No track found.")
            return False

        track.setParentAudioFactor(p)
        self.cancelTextMode()
        self.tts.speak("Ok. Will scale parent audio volume to" + str(p) + " times its original value for the duratino of this track.")
        return True

    self.enableTextMode(self.makeFloatHandler(cont))
    return "Please specify a volume multiplier as a decimal. 1.0 means no change, 0.0 is silence, 1.2 increases volume by 20%."


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





def createCloneTrack(self):
    track = self.getCurrentTrack()
    if track is None:
        return "Need a track to clone!"

    nt = self.makeCloneTrack(track)
    self.appendTrack(nt)
    return "Cloned to track " + nt.getName()




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
    clips = []
    destinationTrack.insertClip(sourceTrack.concatenate(fade=fade, clips=clips))
    return "Ok. Merged clips onto " + destinationTrack.getName()


def mergeTrack2(self, fade=False):
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
    clips = []
    destinationTrack.insertClip(sourceTrack.recConcatenate(self.findChildren))
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

def createVoiceOver2(self):
    # this just uses some moviepy2 features and uses linked tracks
    # will scale down volume by self.quietFactor by default
    # you can emulate the behaviour of this function by going ALT+l, ", <ENTER MESSAGE>, P 0.2
    # put in another factor than 0.2 for different volume scaling
    track = self.getCurrentTrack()
    if track is None:
        return "Cannot create voice over: No track selected."

    clip = self.getCurrentClip()
    if clip is None:
        return "Cannot create voice over without a clip to speak over."

    self.createLinkTrack()
    link = self.getCurrentTrack()
    def cont():
        self.setParentAudioFactor(self.quietFactor)
        self.tts.speak("Created voice over track " + link.getName() + " with audio factor " + str(self.quietFactor) + ". Merge the parent to see the result.")
        return True

    return self.createVoiceClip(cont=cont)








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

def createVoiceClip(self, cont=None):
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
        if cont:
            return cont()
        return True #delete text

    self.enableTextMode(handleVoiceMessage)
    return "Enter the message to be spoken. Enter to submit, escape to cancel."





def copyToHead(self):
    clip = self.getCurrentSubclip()
    if clip is None:
        return "No clip to copy!"


    # this is for more intuitive behaviour when people have just selected a new clip without mark or seek set
    if clip.duration == 0:
        # usually noone wants to copy a 0 duration clip -> let's assume they want the entire current clip instead.
        clip = self.getCurrentClip()
        if clip is None:
            return "Sorry, something went wrong."

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




def switchToWorkspace(self, n):
    if not(n in self.workspaces):
        return "Cannot switch to workspaces: Not a valid workspace."

    if not(self.currentWorkspace in self.workspaces):
        return "Cannot switch workspace: Something is very wrong."

    if not(self.workspaces[self.currentWorkspace][0] == []):
        # this shouldn't come up, but it's better to have a cryptic message than to lose data
        return "Cannot switch workspaces: Stash isn't empty." 

    self.workspaces[self.currentWorkspace] = (self.tracks, self.currentTrack)
    (self.tracks, self.currentTrack) = self.workspaces[n]
    self.workspaces[n] = ([], None)
    self.currentWorkspace = n
    return "Now on workspace " + str(n)


def sendTrack(self, workspace):
    if not(workspace in self.workspaces):
        return "Cannot send track to wworkspace: Invalid workspace."

    track = self.getCurrentTrack()
    if track is None:
        return "Cannot send track to workspace: No track!"

    if workspace == self.currentWorkspace:
        return "Track is already on that workspace. No change."

    otherCurrentTrack = self.workspaces[workspace][1]
    if otherCurrentTrack == None:
        # this happens when we send a track to an otherwise untouched workspace
        otherCurrentTrack = 0

    self.workspaces[workspace] = (self.workspaces[workspace][0] + [track], otherCurrentTrack)
    del self.tracks[self.currentTrack]
    self.shiftFocus((0,-1))
    track.workspacePreference = workspace
    return "Ok. Sent track to workspace " + str(workspace)









def orderTrack(self, direction):
    # move track up or down in display
    track = self.getCurrentTrack()
    if track is None:
        return "Cannot reorder track: No track!"
    l = len(self.tracks)
    if l <= 1:
        return "Not enough tracks to reorder."

    x = self.currentTrack + direction
    if (x < 0): 
        return "Can't reorder. Reached top."
    if (x >= l):
        return "Can't reorder. Reached bottom."

    tmp = self.tracks[x]
    self.tracks[x] = track
    self.tracks[self.currentTrack] = tmp
    self.currentTrack = x
    if direction <= 0:
        return "Moved up with " + track.getDisplayName()
    return "Moved down with " + track.getDisplayName()







def shiftFocus(self, pos):
    (x, y) = pos
    if self.currentTrack is None:
        if self.tracks == []:
            return "No tracks. Please create a new track by hitting n."
        if y >= 0:
            self.currentTrack = len(self.tracks) - 1
        else:
            self.currentTrack = 0
        return self.getCurrentTrack().getDisplayName()


    # sanity, this can come up due to workspace shenanigans
    if (self.currentTrack < 0) or (self.currentTrack >= len(self.tracks)):
        self.currentTrack = None
        return "Whoops. Something got lust in the shuffling. Try again."


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

def whereAmI(self):
    track = self.getCurrentTrack()
    if track is None:
        return "Please create at least 1 track."
    w = track.getName()
    if track.temporary:
        w = "temporary " + w
    w += " at " + track.strIndex()
    if track.hasParent():
        w += " linked to " + track.getParentTrackName() + " at clip " + str(track.getParentTrackIndex())

    clip = self.getCurrentClip()
    if clip is None:
        return w
    w += " at position " + toTimecode(getSeekPos(clip))
    if isAudioClip(clip):
        w += " *audio*"
    if isVideoClip(clip):
        w += " *video*"

    return w

def newTrack(self, name=None, audioOnly=False, temporary=True, file=None):
    if name is None:
        name = "track " + str(len(self.tracks))

    self.appendTrack(Track(name=name, audioOnly=audioOnly, temporary=temporary, file=file))
    self.currentTrack = len(self.tracks)-1
    return "Ok"



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
    return showMark(t)

def isPlaying(self):
    return self.video_flag.is_set()

def playPause(self, seekOnPause=False):
    # check if we're currently playing
    if self.video_flag.is_set():
        self.video_flag.clear()
        self.video_flag = threading.Event()
        self.audio_flag = threading.Event()
        if seekOnPause:
            if self.playclip is None:
                return "" # sanity
            return self.seek(self.playseekpos + self.clock.tick(self.playclip.fps) / 1000)
        return ""


    clip = self.getCurrentClip()
    if not(clip):
        return "No clip to play!"


    if getSeekPos(clip) >= clip.duration:
        return "End of clip."

    self.playseekpos = getSeekPos(clip) # this is only for seekOnPause
    clip = clip.subclip(getSeekPos(clip))
    #fps=15
    audio_fps=22050
    audio_buffersize=3000
    audio_nbytes=2
    if isVideoClip(clip):
        if clip.audio is None:
            return "Clip has no audio."
        clip = clip.audio

    audiothread = threading.Thread(
        target=clip.preview, # important: this is clip.audio.preview for normal video clips
        args=(audio_fps, audio_buffersize, audio_nbytes, self.audio_flag, self.video_flag),
    )
    audiothread.start()
    self.video_flag.set()
    self.audio_flag.wait()
    self.playtime = self.clock.tick(clip.fps) / 1000
    self.playclip = clip


    return ""

        


def createTextClip(self):
    track = self.getCurrentTrack()
    if track is None:
        track = self.newTrack()
        
    clip1 = self.getCurrentClip()
    sz = (1024, 768)    
    if clip1 is not None:
        if isVideoClip(clip1):
            sz = clip1.size

            
    def cont(w):
        clip = TextClip(text=w,
                        font='Ariel',
                        interline=200,
                        bg_color="black",
                        color="white",
                        size=sz,
                        method="caption").with_duration(3)
        track.insertClip(clip)
        self.tts.speak("Created text clip.")
        self.cancelTextMode()
        return True


    self.enableTextMode(cont)
    return "Please enter text to be displayed in clip."

def recordAudioClip(self):
    if self.audiorecorder.isRecording():
        clip = AudioFileClip(self.audiorecorder.stop())
        track = self.getCurrentTrack()
        if track is None:
            track = newTrack()
            msg = "Stopped audio recording and insrted onto new track."
        else:
            msg = "Stopped audio recording and inserted onto track."
        track.insertClip(clip)
        return msg

    # this happens when we are not currently recording
    track = self.getCurrentTrack()
    if track is None:
        return "Please select or create a track."

    self.audiorecorder.start()
    return "Started recording. Hit r again to stop."
        
    


def addTag(self, useMark=False):
    track = self.getCurrentTrack()
    if track is None:
        return "Need a track to add tag to."

    if track.isLocked():
        return "Cannot add tag: Track is locked."
    
    
    clip = track.get()
    if clip is None:
        return "Need a clip to add tag to."

    if useMark:
        pos = getMark(clip)
    else:
        pos = getSeekPos(clip)
        
    def nameCont(w):
        if w == "":
            self.tts.speak("Please enter a name for the tag.")
            return False
        track.tag(name=w, pos=pos)
        self.cancelTextMode()
        self.tts.speak("Tag added.")
        return True

    self.enableTextMode(nameCont)
    return "Please enter a name for the tag at position " + showMark(pos) + "."

def removeTag(self):
    track = self.getCurrentTrack()
    if track is None:
        return "Cannot delete tag: No track!"

    if track.isLocked():
        return "Cannot remove tag: Track is locked."
    
    clip = self.getCurrentClip()
    if clip is None:
        return "Cannot delete tag: No clip selected!"

    tag = track.getCurrentTag()
    if tag is None:
        return "Cannot remove tag: No tag to remove."
    
    track.removeTag(tag.name)
    return "Deleted tag " + tag.name + " at position " + showMark(pos)
    

def nextTag(self, prev=False):
    track = self.getCurrentTrack()
    if track is None:
        return "Cannot cycle tag without a track."

    track.nextTag(prev=prev)
    return self.showTag()

def showTag(self):
    track = self.getCurrentTrack()
    if track is None:
        return "No tag because there is no track!"

    clip = self.getCurrentTrack()
    if clip is None:
        return "No tag because there is no clip!"

    tag = track.getCurrentTag()
    if tag is None:
        return "No tags for clip."

    return tag.name + " at " + showMark(tag.pos)
    
def seekTag(self, useMark=False):
    track = self.getCurrentTrack()
    if track is None:
        return "Cannot jump to tag without a track!"

    clip = self.getCurrentClip()
    if clip is None:
        return "Cannot jump to tag without a clip!"

    tag = track.getCurrentTag()
    if tag is None:
        return "Cannot jump: No tags for clip."

    if useMark:
        setMark(clip, tag.pos)
        return "set mark to tag " + tag.name + " at position " + showMark(tag.pos)
    self.seek(tag.pos)
    return "seek to tag " + tag.name + " at position " + showMark(tag.pos)
