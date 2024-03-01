
import shutil, sys, os
from tempfile import mkstemp, mktemp, NamedTemporaryFile
from moviepy.editor import *
from datetime import timedelta
import random, json
import subprocess
import wave
import tanto

def toTimecode(seconds):
    return str(timedelta(seconds=seconds))

def isAudioFile(filename):
    ws = filename.split(".")
    extensions= "wav mp3 ogg flac".split(" ")
    return ws[-1].lower() in extensions

def isVideoFile(filename):
    return not(isAudioFile(filename))



def makeCompositeAudioClip(clips, offset=0):
    if not(clips):
        return None

    for i in range(1, len(clips)):
        clips[i] = clips[i].with_start(offset)


    return CompositeAudioClip(clips)

    


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

def ensureExtension(file, default=".mkv"):
    (w, ext) = os.path.splitext(file)
    if ext == "":
        return w + default
    return file

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


    

        

        


nato_alphabet = "Alpha, Bravo, Charlie, Delta, Echo, Foxtrot, Golf, Hotel, India, Juliett, Kilo, Lima, Mike, November, Oscar, Papa, Quebec, Romeo, Sierra, Tango, Uniform, Victor, Whiskey, X-ray, Yankee, Zulu".lower().split(", ")
name_delim = "-"


def ensureBitrateString(x):
    w = str(x)
    if w.endswith("k"):
        return w
    return w+ "k"

    
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

def extendNato(name, nextNato):
    # 21-whiskey-somenameblabla -> 21-alpha-whiskey-somenameblabla
    (number, nato, rest) = getNamePrefixes(name)    
    return name_delim.join([number, nextNato, nato, rest])

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

def isInt(w):
    return w.isdigit()


def partitionClips(clips):
    aclips = []
    vclips = []
    for clip in clips:
        if isAudioClip(clip):
            aclips.append(clip)
            continue
        vclips.append(clip)
    return (vclips, aclips)
    
        

def truncateFloatString(w, n=2):
    """Truncates a string like "0.00000002001" to a given number of decimals, e.g. "0.00" with n=2."""
    if "." not in w:
        return w
    
    ws = w.split(".")
    ws[-1] = ws[-1][:n]
    return ".".join(ws)

def showMark(mark):
    if mark > 60 * 60:
        return truncateFloatString(toTimecode(mark)    )
    if mark > 60:
        ws = truncateFloatString(toTimecode(mark)).split(":")
        mcount = "minute " if ws[1] == "01" else "minutes "
        scount = "second" if ws[2] == "01" else "seconds"
        return ws[1] + mcount + ws[2] + truncateFloatString(scount)
    return truncateFloatString(str(mark)) + " seconds"    


def padZero(w, num_zeroes=10):
    return "0"*(num_zeroes - len(w)) + w


def inWindow(n, window=(0,0)):
    (a, b) = window
    return (n >= a) and (n < b)

def moveWindow(n, window):
    (a, b) = window
    return (a+n, b+n)

def mkTempThemeFile():
    """Creates a temporary theme file with injected data/ locations. This can be used when user supplies no local theme.json. Returns the NamedTemporaryFile object of the created theme file."""
    theme_string = open(tanto.get_tanto_data("theme.json"), "r").read()
    # next line is confusing: we replace all ocurrences of e.g. fontfile = "data/blabla.font" with fontfile = "home/someuser/somenv/site/packageblabla/tanto/data/blabla.font"
    # then load it as actual json
    theme = json.loads(theme_string.replace('"data/', '"' + tanto.get_tanto_data("")))
    f = NamedTemporaryFile("w", delete=False)
    f.write(json.dumps(theme))
    f.close()
    return f
                      

def printerr(w, **kwargs):
    print(w, file=sys.stderr, **kwargs)

