

from moviepy.editor import *
from datetime import timedelta

def toTimecode(seconds):
    return str(timedelta(seconds=seconds))

def getSeekPos(clip):
    if not("seekpos" in clip.__dict__):
        return 0
    return clip.seekpos


def setSeekPos(clip, pos):
    clip.seekpos = pos
    
def getMark(clip):
    if not("mark" in clip.__dict__):
        return 0
    return clip.mark

def setMark(clip, mark):
    clip.mark = mark


def isAudioClip(clip):
    return isinstance(clip, AudioClip)

def isVideoClip(clip):
    return isinstance(clip, VideoClip)


def isAudioFile(filename):
    ws = filename.split(".")
    extensions= "wav mp3 ogg flac".split(" ")
    return ws[-1].lower() in extensions

def isVideoFile(filename):
    return not(isAudioFile(filename))




def makeCompositeAudioClip(clips):
        # there's a bug in moviepy with audio fps, so we have to workaround
    if not(clips):
        return None

    tmp = CompositeAudioClip(clips)
    x = clips[0]
    tmp.fps = x.fps    
    return tmp
    
