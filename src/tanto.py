#!/bin/python

# Tanto - Terminal based Video and Audio editing tool

import sys, os, glob, threading, multiprocessing, time
import traceback
import logging
from unittest.mock import Mock

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
from tanto_audiorecorder import AudioRecorder
from tanto_gui import *
import _interactive
import _keybindings

TANTO_VERSION = "0.1.0"
class ViewState(object):
    def __init__(self, res=(0,0), ui=None, tts=None, projectdir="./", textinput=None):
        self.debug = True
        self.ui = TantoGui(res=res, manager=ui)
        self.lastMsg = ""
        self.clock = pygame.time.Clock()
        self.textinput = textinput
        self.audiorecorder = AudioRecorder()
        self.projectdir = projectdir
        self.running = True
        self.tts = tts
        self.graveyard = Track(name="graveyard", locked=True)
        self.tracks = [self.graveyard]
        self.head = None
        self.headOverride = False
        self.specialOverrideMsg = "Override..."
        self.currentTrack = None
        self.clipboard = None
        self.saveMark = None
        self.video_flag = threading.Event()
        self.audio_flag = threading.Event()
        self.isRecordingAudio = False
        self.audioData = None

        self.quietFactor = 0.2
        self.smallTimeStep = 1 # in seconds
        self.largeTimeStep = 60 # in seconds
        self.volumeStep = 0.1
        self.textmode = False
        self.defaultTextHandler = lambda w: True
        self.handleText = self.defaultTextHandler
        
        # FIXME: this doesn't need to happen in the constructor, but since this is basically a signleton, we extend here for naming convenience (so we can use 'self')
        _interactive.extend(self)
        self.cmds = {}
        self.help={}
        for (key, f, category, shortdesc) in _keybindings.stdKeybindings(self):
            self.cmds[key] = f
            self.help[key] = (category, shortdesc)
            

        for n in list(range(0,10)):
            self.cmds[str(n)] = lambda n=n: self.seekPercentage(n*10)
            self.help[str(n)] = (_keybindings.C_SEEK, "seek to " + str(n*10) + "% of selected clip.")
            self.cmds["ALT+" + str(n)] = lambda n=n: self.setMarkPercentage(n*10)
            self.help["ALT+"+str(n)] = (_keybindings.C_EDIT, "set the mark at " + str(n*10) + "% of the selected clip.")

        # workspaces
        self.num_workspaces = 4
        self.currentWorkspace = 1
        self.workspaces = {i : ([], None) for i in range(1, self.num_workspaces+1)}
        
        for n in list(range(1, self.num_workspaces+1)):
            self.cmds["F"+str(n)] = lambda n=n: self.switchToWorkspace(n)
            self.help["F"+str(n)] = (_keybindings.C_WORKSPACE, "switch to workspace " + str(n) + ".")
            self.cmds["CTRL+" + str(n)] = lambda n=n: self.sendTrack(n)
            self.help["CTRL+"+str(n)] = (_keybindings.C_WORKSPACE, "send selected track to workspace " + str(n) + ".")

        # finally, loading project
        if self.projectdir:
            self.loadDir(self.projectdir)
            

    def loadDir(self, dir):
        for file in sorted(glob.glob(dir + "/*"), key= lambda w: padZero(w)):
            if os.path.isdir(file):
                nt = Track.fromDir(file)
                nt.temporary = False
                nt.loadVars(self.projectdir)
                self.tracks.append(nt) # not a mistake
                tmp = self.currentTrack
                self.currentTrack = len(self.tracks) - 1
                self.sendTrack(nt.workspacePreference)
                self.currentTrack = tmp
                

            else:
                self.loadFile(file)
                
            
    def loadFile(self, file):
        name = trackNameFromFile(file, "track " + str(len(self.tracks)))            
        self.newTrack(name=name, audioOnly=isAudioFile(file), temporary=False, file=file)
        track = self.getCurrentTrack()
        track.insertFile(file)
        track.left()



        
    def save(self, file=None):
        pass


    def _getClipboard(self):
        return self.clipboard

    def _putClipboard(self, clip):
        if self.clipboard is not None:
            self.graveyard.insertClip(self.clipboard)
        self.clipboard = clip
        
    
    def _allTracks(self):
        acc = []
        for (tracks, x) in list(self.workspaces.values()):
            for track in tracks:
                acc.append(track)
        return acc + self.tracks

    def _nameExists(self, trackname):
        return list(filter(lambda otherName: trackname == otherName, [track.getName() for track in self._allTracks()])) != []
        
    
    def storeTrackVars(self):
        for track in list(filter(lambda t: not(t.temporary), self._allTracks())):
            track.storeVars(self.projectdir)


    def findTrackIndices(self, track):
        # return pair of (trackindex, workspaceindex)
        for (k, tracks) in self.workspaces.items():
            if k == self.currentWorkspace:
                tracks = self.tracks

            for i in range(0, len(tracks)):
                if tracks[i] == track:
                    return (i, k)
        return None
            
            
   
    def findTrack(self, trackname):
        tracks = list(filter(lambda t: t.name == trackname, self.tracks))
        if tracks == []:
            return None
        return tracks [0]

    def getParentClip(self, track):
        if not(track.hasParent()):
            return None
        
        (parentname, parentindex) = (track.getParentTrackName(), track.getParentTrackIndex())
        parenttrack = self.findTrack(parentname)
        if parenttrack is None:
            return None

        return parenttrack.get(parentindex)

    def getCurrentLinkedTracks(self):
        clip = self.getCurrentClip()
        track = self.getCurrentTrack()
        if (clip is None) or (track is None):
            return []

        return self.findChildren(track)
    

    def findChildren(self, track, index=None):
        if index is None:
            index = track.index
        acc = []
        for otherTrack in self.tracks:
            if otherTrack.hasParent():
                if (otherTrack.getParentTrackName() == track.name) and (otherTrack.getParentTrackIndex() == index):
                    acc.append(otherTrack) 
        return acc

    def disableHeadOverride(self):
        self.headOverride = False
    
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
            afterclip = clip.subclip(0,0)
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
        
        
    
    def makeCloneTrack(self, track):
        newTrack = track.clone()
        newTrack.temporary = True
        newTrack.name = self.makeSubTrackName(track)
        return newTrack


    def makeSideTrack(self, track):
        newTrack = track.clone()
        newTrack.name = self.makeSideTrackName(track)
        return newTrack
    

    def makeSubTrackName(self, track):
        name = subTrackName(track.getName())
        allNames = [track.getName() for track in self._allTracks()]
        while True: # we *will* name this
            if not(name in allNames):
                return name
            name = sideTrackName(name)

    def makeSideTrackName(self, track, index=None):
        name = sideTrackName(track.getName(), index)
        allNames = [track.getName() for track in self._allTracks()]
        while True:
            if not(name in allNames):
                return name
            name = sideTrackName(name)
                    
                
    def makeLinkTrackName(self, track, index=None):
#        name = sideTrackName(track.getName(), index)
        name = makeNatoName(str(index), natoPrefixForLetter("a"), track.getName())
        allNames = [track.getName() for track in self._allTracks()]
        initial = name
        while True:
            if not(name in allNames):
                return name
            name = subTrackName(name)
            if name == initial:
                # prevent infinite loop
                name = extendNato(name, natoPrefixForLetter("a"))
                initial = name

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

    def getCurrentTrack(self):
        if self.headOverride:
            return self.head
            
        if self.currentTrack is None:
            return None

        if (self.currentTrack < 0) or (self.currentTrack >= len(self.tracks)):
            return None

        return self.tracks[self.currentTrack]


    def appendTrack(self, track):
        track.workspacePreference = self.currentWorkspace
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

    def updateUI(self):
        override = None
        if self.isTextMode():
            override = self.textinput
        self.ui.drawEverything(self.currentWorkspace, self.workspaces, self.lastMsg, self.currentTrack, self.head, self.tracks, override=override)


        
def getKeyRepresentation(event):
    # we like keys as simple strings with all modifiers like so "CTRL+ALT+ENTER" etc.
    w = ""
    d = {K_RETURN : "ENTER", K_SPACE : "SPACE", K_TAB : "TAB", K_BACKSPACE : "BACKSPACE", K_F1 : "F1", K_F2 : "F2", K_F3 : "F3", K_F4 : "F4"}
    keystring = d.get(event.key, event.unicode)

    
    keys = pygame.key.get_pressed()
    if keys[K_LCTRL] or keys[K_RCTRL]:
        w += "CTRL+"
        if not(event.key in d):
            keystring = pygame.key.name(event.key) #unicode representation is messed up when some modifiers are present

    if keys[K_LALT] or keys[K_RALT]:
        w += "ALT+"
        if not(event.key in d):        
            keystring = pygame.key.name(event.key)

    # FIXME: do shift?
    
    return w + keystring




def makeHelpText():
    w = "tanto - lightweight, accessible audio and video editor\nversion " + TANTO_VERSION + "\n\n"
    w += "Usage:\n  tanto /path/to/dir\nOpen tanto in directory, loading all files and tracks in the directory.\n tanto\nInvoked without argument, will assume the current directory to be the working directory.\n  tanto -h\nPrint this help.\n\ntanto doesn't work with project files. Tanto works with files and directories. You may want to create a 'project directory', by creating a new directory and copying video and audio files you wish to edit into it, then invoking tanto with the directory as argument.\n\nBelow is a list of keybindings and commands inside tanto.\n"
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



def main(argv):
    if len(argv) >= 2:
        if (argv[1] == "-h") or (argv[1] == "--help"):
            print(makeHelpText())
            return
    

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

    st = ViewState(tts=Speaker(), res=(xres, yres), ui=pygame_gui.UIManager((xres, yres), "theme.json"), projectdir=projectdir, textinput=textinput)     
    while st.running:
        time_delta = clock.tick(60)/1000.0
        events = pygame.event.get()
        textinput.update(events)
#        screen.blit(textinput.surface, (10, yres-20))        
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
                    try:
                        # FIXME: this is a bit strong, but we don't want to lose data
                        msg = f()
                    except Exception as e:
                        logging.error(traceback.format_exc())
                        msg = "exception"

                    st.updateUI()
                    if msg != st.specialOverrideMsg:
                        st.disableHeadOverride() # ctrl+j is for one command only
                    if msg:
                        st.lastMsg = msg                        
                        st.tts.speak(msg)
                        if not(st.isTextMode()):
                            textinput.value = msg

            if event.type == QUIT:
                st.quit()

            st.ui.manager.process_events(event)



        st.ui.manager.update(time_delta)
        st.ui.manager.draw_ui(screen)            
        screen.fill(pygame.color.THECOLORS["black"])
        pygame.display.update()
        

    # cleanup
    pygame.quit()
    sys.exit()




if __name__ == "__main__":        
    main(sys.argv)


    


