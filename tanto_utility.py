

from moviepy.editor import *
from datetime import timedelta

def toTimecode(seconds):
    return str(timedelta(seconds=seconds))


def getFilepath(clip):
    if not("filepath" in clip.__dict__):
        return None
    return clip.filepath

def setFilepath(clip, filepath):
    clip.filepath = filepath
    
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




def makeCompositeAudioClip(clips, offset=0):
        # there's a bug in moviepy with audio fps, so we have to workaround
    if not(clips):
        return None

    for i in range(1, len(clips)):
        clips[i] = clips[i].set_start(offset)
    
    tmp = CompositeAudioClip(clips)
    x = clips[0]
    tmp.fps = x.fps    
    return tmp

def resetClipPositions(clip):
    setSeekPos(clip, 0)
    setMark(clip, 0)
    


def isTantoFile(file):
    ws = file.split(".")
    return ws[-1] == "tanto"


def trackNameFromFile(file, alternative="untitled"):
    ws = file.split("/")
    if ws:
        name = ws[-1]
        name.replace(" ", "-")
    else:
        name = alternative
    return name

def getExtension(file):
    ws = file.split(".")
    return ws[-1]


def writeClip(clip, file):
    ext = getExtension(file)
    if ext == "mkv":
        clip.write_videofile(file, codec="libx264")
        return

    if isVideoClip(clip):
        clip.write_videofile(file)
        return

    if isAudioClip(clip):
        clip.write_audiofile(file)
        

        

        
