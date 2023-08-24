

from moviepy.editor import *



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
