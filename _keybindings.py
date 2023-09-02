


# categories
C_PROGRAM = "Program"
C_NAVIGATION = "Navigation"
C_EDIT = "Editing"
C_WORKSPACE = "Workspaces"


def stdKeybindings(self):
    return [
        ("q", self.quit),
        ("Q", self.save),
        ("ENTER", self.setMark),
        ("TAB", self.switchHead),
        ("ALT+ENTER", self.setHeadOffset),
        ("BACKSPACE", self.jumpToMark),
        ("CTRL+e", lambda: self.seekPercentage(100)),
        ("ALT+e", self.setMarkEnd),
        ("CTRL+a", lambda: self.seekPercentage(0)),
        ("ALT+a", self.setMarkStart),
        ('"', self.createVoiceClip),
        ("!", self.createSilenceClip),
        ("§", self.createVoiceOver),
        ("$", lambda: self.createVoiceOver(file=True)),
        ("ALT+v", self.createVoiceOver2),
        (";", self.renameTrack),
        ("=", self.setVolume),
        ("SPACE", self.playPause),
        ("CTRL+SPACE", lambda: self.playPause(seekOnPause=True)),
        ("j", self.setHead),
        ("J", self.whereIsHead),
        ("CTRL+j", self.toggleHeadOverride),
        ("CTRL+x", self.cutClip),
        ("CTRL+c", lambda: self.cutClip(copy=True)),
        ("y", self.saveMark),
        ("CTRL+v", self.paste),
        ("CTRL+y", self.pasteMark),
        ("v", self.bisect),
        ("V", lambda: self.bisect(inPlace=True)),
        ("c", self.copyToHead),
        ("ALT+c", self.createCloneTrack),
        ("m", self.mergeTrack2),
        ("M", lambda: self.mergeTrack(fade=True)),
        ("i", self.mixAudio),
        ("I", lambda: self.mixAudio(inPlace=True)),
        ("p", lambda: self.setParentAudioFactor(self.quietFactor)),
        ("P", self.setParentAudioFactor),
        ("CTRL+p", lambda: self.shiftFocus((0, -1))),
        ("CTRL+n", lambda: self.shiftFocus((0, 1))),
        ("CTRL+f", lambda: self.shiftFocus((1, 0))),
        ("CTRL+b", lambda: self.shiftFocus((-1, 0))),
        ("ALT+p", lambda: self.orderTrack(-1)),
        ("ALT+n", lambda: self.orderTrack(1)),
        ("+", lambda: self.changeVolume(self.volumeStep)),
        ("-", lambda: self.changeVolume((-1) * self.volumeStep)),
        ("S", self.saveClip),
        ("_", self.saveTrack),
        ("CTRL+d", self.removeClip),
        ("ALT+d", self.removeTrack),
        ("CTRL+l", self.toggleLock),
        ("ALT+l", self.createLinkTrack),
        ("<", self.minFocus),
        (">", self.maxFocus),
        ("a", lambda: self.shiftFocus((-1,0))),
        ("s", lambda: self.shiftFocus((0, 1))),
        ("w", lambda: self.shiftFocus((0, -1))),
        ("d", lambda: self.shiftFocus((1,0))),
        ("n", self.newTrack),
        ("h", self.whereAmI),
        ("H", self.printDebug),
        ("t", self.whereMark),
        ("^", lambda: self.stepFactor(0.1)),
        ("´", lambda: self.stepFactor(10)),
        ("f", lambda: self.seekRelative(self.smallTimeStep)),
        ("b", lambda: self.seekRelative((-1)*self.smallTimeStep)),
        ("F", lambda: self.seekRelative(self.largeTimeStep)),
        ("B", lambda: self.seekRelative((-1)*self.largeTimeStep))
        ]
