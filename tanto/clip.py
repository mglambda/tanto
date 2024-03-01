import os, subprocess, shutil
from tempfile import NamedTemporaryFile
from subprocess import run
from moviepy.editor import *
from tanto.tanto_utility import *
from tanto.definitions import *

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



def writeClip(clip, file, **kwargs):
    ext = getExtension(file)
    tmpfile = mktemp() + "." + ext

    if ext == "mkv":
        clip.write_videofile(tmpfile, codec="libx264", **kwargs)
    elif isVideoClip(clip):
        clip.write_videofile(tmpfile, **kwargs)
    elif isAudioClip(clip):
        clip.write_audiofile(tmpfile, **kwargs)

    # have to do it like this, since moviepy has a bug when you want to write to the same file that a clip is based on (causes freeze frame)
    shutil.move(tmpfile, file)


def getVideoBitrate(clip, file="", default="8000k"):
    if isAudioClip(clip):
        return default
    
    # moviepy has trouble getting bitrate for individual streams in mkv files. They do know the global bitrate though, which is usually correct-ish
    # for other formats it might work though, so let's try
    if "reader" not in clip.__dict__:
        return default
    
    if clip.reader.bitrate is not None:
        return ensureBitrateString(clip.reader.bitrate)

    bitrate = None
    if "video_bitrate" in clip.reader.infos:
        bitrate = clip.reader.infos["video_bitrate"]
        
    if "bitrate" in clip.reader.infos:
        bitrate = clip.reader.infos["bitrate"]

    if bitrate is not None:
        return ensureBitrateString(bitrate)

    # FIXME: in the future we might use file to figure it out ourselves
    return default

def getAudioBitrate(clip, file="", default="50000k"):
   
    if isVideoClip(clip):
        clip = clip.audio


    if clip is None:
        # can happen on e.g. text clips
        return default
        
    if "reader" not in clip.__dict__:
        return default
        
    if clip.reader.bitrate is not None:
        return ensureBitrateString(clip.reader.bitrate)

    bitrate = None
    if "bitrate" in clip.reader.infos:
        bitrate = clip.reader.infos["bitrate"]

    if "audio_bitrate" in clip.reader.infos:
        bitrate = clip.reader.infos["audio_bitrate"]


    if bitrate is not None:
        return ensureBitrateString(bitrate)
    # FIXME: in the future we might use file here    
    return default
    
    

def saveClip(clip, file, video_bitrate=global_video_bitrate, audio_bitrate=global_audio_bitrate):
    """Save a given clip to a file with the provided path. If file doesn't have an extension (like .wav or .mkv), a default extension will be appended to the filename, depending on wether it is an audio or video clip."""
    if not("fps" in clip.__dict__) or (clip.fps == None):
        print("Warning in saveClip: clip has no fps set. Choosing default of " + str(global_fps))
        clip = clip.with_fps(global_fps)

    if clipfile := getFilepath(clip):
        # clip has a file associated with it. It's either temp, or an already existing file we don't want to touch
        if clipfile not in global_temp_clips:
            printerr("warning in saveClip: Attempting to save file with write protected file path '" + clipfile + "'. Refusing to save.")
            return

        # there are many combinations here with extensions on file and clipfile. we simplify by just brutalizing the file and adding the tmpfile extension to whatever file was
        # it might still be that tmpfile had no extension. That's a bug, but oh well. No easy way of determining audio/video on clipfile, so we default to mkv
        (_, ext) = os.path.splitext(clipfile)
        file1 = ensureExtension(file + ext, default=".mkv")
        shutil.move(clipfile, file1)
        global_temp_clips.remove(clipfile)
        return

    # clip has no origin, was probably created during program execution
    if isVideoClip(clip):
        file1 = ensureExtension(file, default=".mkv")
        writeClip(clip, file1,
                  bitrate=video_bitrate,
                  audio_bitrate=audio_bitrate)
    else:
        file1 = ensureExtension(file, ".wav")
        writeClip(clip, file1,
                  bitrate=audio_bitrate)
