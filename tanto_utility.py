
from tempfile import mkstemp
from moviepy.editor import *
from datetime import timedelta
import random
import subprocess
import wave

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

def setChildTracks(clip, tracks):
    clip.childTracks = tracks

def getChildTracks(clip):
    if "childTracks" in clip.__dict__:
        return clip.childTracks
    return []


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


def getAudioClip(clip):
    if isAudioClip(clip):
        return clip
    return clip.audio


def makeCompositeAudioClip(clips, offset=0):
    if not(clips):
        return None

    for i in range(1, len(clips)):
        clips[i] = clips[i].with_start(offset)


    return CompositeAudioClip(clips)

def resetClipPositions(clip):
    setSeekPos(clip, 0)
    setMark(clip, 0)
    return clip

    


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
        

        

        


nato_alphabet = "Alpha, Bravo, Charlie, Delta, Echo, Foxtrot, Golf, Hotel, India, Juliett, Kilo, Lima, Mike, November, Oscar, Papa, Quebec, Romeo, Sierra, Tango, Uniform, Victor, Whiskey, X-ray, Yankee, Zulu".lower().split(", ")
name_delim = "-"


def natoPrefixForLetter(w):
    if w == "":
        return ""

    for v in nato_alphabet:
        if w[0].lower() == v[0]:
            return v

    return nato_alphabet[-1]
        

def getNamePrefixes(w):
    number = ""
    nato = ""
    rest = w
    ws = w.split(name_delim)
    if len(ws) >= 3:
        if ws[0].isdigit():
            number = ws[0]
            
        if ws[1] in nato_alphabet:
            nato = ws[1]

        rest = name_delim.join(ws[2:])
    elif len(ws) == 2:
        if ws[0].isdigit():
            number = ws[0]
            rest = ws[1]
        elif ws[0] in nato_alphabet:
            nato = ws[0]
            rest = ws[1]


    return (number, nato, rest)

def makeNatoName(number, nato, rest):
    ws = [number, nato, rest]
    vs = list(filter(bool, ws))
    return name_delim.join(vs)

def nextNumber(numberstring):
    if numberstring.isdigit():
        try:
            n = int(numberstring)
        except:
            return "0"
        return str(n+1)
    return "0"

def next_alpha(s):
    return chr((ord(s.upper())+1 - 65) % 26 + 65)


def nextNato(natostring):
    if not(natostring):
        return randomNato()
    c = natostring[0]    
    return natoPrefixForLetter(next_alpha(c))

def randomNato():
    return random.choice(nato_alphabet)
    
def subTrackName(name):
    (number, nato, rest) = getNamePrefixes(name)
    return makeNatoName(number, nextNato(nato), rest)

def assertInt(w):
    try:
        n = int(w)
    except:
        return 0
    return n

def sideTrackName(name, n=None):
    (number, nato, rest) = getNamePrefixes(name)
    if n:
        return makeNatoName(str(n), nato, rest)        
    return makeNatoName(nextNumber(number), nato, rest)

def getTTSProgram():
    voxin = "voxin-say"
    try:
        subprocess.run(voxin)
    except FileNotFoundError:
        return None
    return "voxin-say"

def runTTSProgram(prog, w):
    # returns none if unsuccessful, tuple of (result, TMPWAVEFILE) otherwise
    if prog == "voxin-say":
        (x, tmptxtfile) = mkstemp(text=True)
        f = open(tmptxtfile, "w")
        f.write(w)
        f.flush()
        (x2, tmpwavfile) = mkstemp()
        r = subprocess.run([prog, "-f", tmptxtfile, "-w", tmpwavfile])
        return (r, tmpwavfile)
    return None

def makeVoiceClip(w):
    prog = getTTSProgram()
    if not(prog):
        return None

    maybeResult = runTTSProgram(prog, w)
    if maybeResult is None:
        return None

    (r, tmpwavfile) = maybeResult
    if not(r):
        return None
    clip = AudioFileClip(tmpwavfile)
    return clip
    
def makeSilenceClip(duration):
    # Open a (new if necessary) wave file for binary writing
    (fh, tmpfilename) = mkstemp()
    outf = wave.open(tmpfilename, "wb")
    framerate = 48000
    bytesperframe = 2 # 2 -> 16 bit
    outf.setframerate(48000)
    outf.setnchannels(1)
    outf.setnframes(int(duration * framerate))
    outf.setsampwidth(bytesperframe)
    outf.writeframes(bytes(0 for i in range(int(duration * framerate) * bytesperframe)))


    clip = AudioFileClip(tmpfilename)
    return clip


def isFloat(w):
    return w.replace(".", "0").replace("-","0").isdigit()



def partitionClips(clips):
    aclips = []
    vclips = []
    for clip in clips:
        if isAudioClip(clip):
            aclips.append(clip)
            continue
        vclips.append(clip)
    return (vclips, aclips)
    
        


def showMark(mark):
    if mark > 60:
        return toTimecode(mark)
    return str(mark) + " seconds"    
