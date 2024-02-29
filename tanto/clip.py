import os, subprocess
from tempfile import NamedTemporaryFile
from subprocess import run
from moviepy.editor import *

# I don't like the python tempfile architecture, it makes me do things like this

global_temp_clips = []
# so subclassing is not nice in python. yeah.
# this is a collection of functions that essentially extend the moviepy clip class

def getFilepath(clip):
    if not("filepath" in clip.__dict__):
        return None
    return clip.filepath

def setFilepath(clip, filepath):
    clip.filepath = filepath

def isFileClip(clip):
    return getFilepath(clip) is not None

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

def setChildTracks(clip, tracks):
    clip.childTracks = tracks

def getChildTracks(clip):
    if "childTracks" in clip.__dict__:
        return clip.childTracks
    return []


def isAudioClip(clip):
    return isinstance(clip, AudioClip)

def isVideoClip(clip):
    return (isinstance(clip, VideoClip) or isinstance(clip, TextClip))


def resetClipPositions(clip):
    setSeekPos(clip, 0)
    setMark(clip, 0)
    return clip



def getAudioClip(clip):
    if isAudioClip(clip):
        return clip
    return clip.audio

def ffmpeg_run(args, input=None, output="out.mkv"):
    if input is not None:
        inputargs = ["-i", input]
    else:
        inputargs = []

    cmd = ["ffmpeg", "-y"] + inputargs + args + [output]
    return subprocess.run(cmd) # add capture_output=True to supress spam

def ffmpeg_subclip(clip, start, end=None):
    if end is None:
        end = clip.duration

    file = getFilepath(clip)
    if file is None:
        raise FileNotFoundError("ffmpeg_subclip called without an associated file.")
    
    (_, extension) = os.path.splitext(file)
    # FIXME: this tmpfile isn't being deleted. in some cases that may eventually cause trouble
    f = NamedTemporaryFile(suffix=extension, delete=False)
    global_temp_clips.append(f.name)
    r = ffmpeg_run(["-ss", str(start), "-to", str(end), "-c", "copy"], input=file, output=f.name)

    if isVideoClip(clip):
        out = VideoFileClip(f.name)
    else:
        out = AudioFileClip(f.name)

    setFilepath(out, f.name)
    return out
