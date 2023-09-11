
import os, glob
from moviepy.editor import *
from tanto_utility import *
import copy

class Tag(object):
    def __init__(self, name="", pos=0):
        self.name = name
        self.pos = pos

    def __str__(self):
        return "Tag(name='" + self.name + "', pos=" + str(self.pos) + ")"

    def __repr__(self):
        return str(self)
        

class Track(object):

    storable = "parent parentAudioFactor audioOnly index offset locked workspacePreference tags size".split(" ")
    def __init__(self, file=None, name=None, audioOnly=False, locked=False, parent=None, offset=0, workspacePreference=1, temporary=True, parentAudioFactor=None, tags={}, size=None):
        self.file = file
        self.temporary = temporary
        self.tags = tags
        self.parentAudioFactor = parentAudioFactor
        self.workspacePreference = workspacePreference
        self.locked = locked
        self.size = size
        self.offset = offset
        self.parent = parent
        self.name = name
        self.audioOnly = audioOnly
        self.data = []
        self.index = None
        self.fadeDuration = 1.0

    def isLocked(self):
        return self.locked

    def lock(self):
        self.locked = True

    def unlock(self):
        self.locked = False

    def tag(self, name="", pos=0):
        tag = Tag(name=name, pos=pos)
        
        if self.index is None:
            # this is kind of special, like tagging the track itself
            index = -1
        else:
            index = self.index

        tags = self.tags.get(self.index, [])
        self.tags[index] = sorted(tags + [tag], key=lambda t: t.pos)
        if tags == []:
            return
        first = tags[0]
        while self.getCurrentTag() != first:
            self.nextTag()

    def nextTag(self, prev=False):
        tags = self.tags.get(self.index, [])
        if tags == []:
            return None
        if prev:
            self.tags[self.index] = tags[-1:] + tags[0:-1]
        else:
            self.tags[self.index] = tags[1:] + tags[0:1]
        return self.tags[0]
        
    def removeTag(self, name):
        tags = self.tags.get(self.index, [])
        self.tags[index] = [t for t in tags if t.name != name]


    def getCurrentTag(self):
        tags = self.tags.get(self.index, [])
        if tags == []:
            return None
        return tags[0]
    
                         
        
    def getParentTrackName(self):
        if self.parent is None:
            return None
        return self.parent[0]

    def getParentTrackIndex(self):
        if self.parent is None:
            return None
        return self.parent[1]

    def getSize(self):
        return self.size
    
    
    def setSize(self, size):
        self.size = size
    
    def setParent(self, trackname, index):
        self.parent = (trackname, index)
        
    def hasParent(self):
        return not(self.parent is None)

        
    def setParentAudioFactor(self, factor):
        self.parentAudioFactor = factor

    def getParentAudioFactor(self):
        return self.parentAudioFactor
    
    def isAudioOnly(self):
        return self.audioOnly
        
    def right(self):
        if self.index is None:
            return
        
        if self.index+1 <= len(self.data):
            self.index += 1

    def left(self):
        if self.index is None:
            return
        
        if self.index-1 >= 0:
            self.index -= 1



    def setOffset(self, offset):
        self.offset = offset
            
    def getOffset(self):
        return self.offset
        
            
                
            
    def getName(self):
        return self.name


    def getDisplayName(self):
        w = self.getName()[:50]

        if self.hasParent():
            if self.getOffset() > 0:
                offsetstr = showMark(self.getOffset())
            else:
                offsetstr = ""
            w = "*link " + offsetstr + "* " + w
            
        if self.isAudioOnly():
            w += " *audio*"

        if self.file:
            w += " *file*"

        if self.temporary:
            w = "& " + w

        if self.isLocked():
            w = "%" + w
        return w
                


    def rewind(self):
        self.index = 0
        
    def empty(self):
        return len(self.data) == 0

    def get(self, index=None):
        if index:
            # thread safe can suck a fat one
            tmp = self.index
            self.index = index
            res = self.get()
            self.index = tmp
            return res #FIXME obviously
        
            
            
            
        
        if self.index is None:
            return None

        if self.index >= len(self.data):
            return None
        return self.data[self.index]
        
    def atEnd(self):
        if self.index is None:
            return True
        else:
            return self.index >= len(self.data)


    def fromDir(filepath):
        files = list(filter(lambda w: w[0:1] != ".", sorted(os.listdir(filepath), key=lambda w: padZero(w))))
        track = Track(name=trackNameFromFile(filepath))        
        for filename in files:
            file = filepath + "/" + filename
            if os.path.isdir(file):
                continue
            track.insertFile(file)

        if len(list(filter(isAudioClip, track.data))) == len(track.data):
            track.audioOnly = True
        return track

    def loadVars(self, projectdir):
        if self.file:
            dir = projectdir + "/." + os.path.basename(self.file)
        else:
            dir = projectdir + "/" + self.name

        if not(os.path.isdir(dir)):
            return

        for key in Track.storable:
            file = dir + "/." + key
            if not(os.path.isfile(file)):
                continue
            w = open(file, "r").read()
            tmp = self.__dict__[key]
            try:
                self.__dict__[key] = eval(w)
            except:
                self.__dict__[key] = tmp
                
            
            
        
    
    def storeVars(self, projectdir):
        dir = self.assertDir(projectdir)
        for key in Track.storable:
            filename = "." + key
            f = open(dir + "/" + filename, "w")
            f.write(str(self.__dict__[key]))
            f.close()
            
    def save(self, projectdir):
        self.temporary = False        
        self.storeVars(projectdir)        
        if self.file:
            return


        dir = self.assertDir(projectdir)
        for i in range(len(self.data)):
            clip = self.data[i]
            # clip has no origin, was probably created during program execution
            if isVideoClip(clip):
                writeClip(clip, dir + str(i) + ".mkv")
            else:
                writeClip(clip, dir + str(i) + ".wav")

                
    def assertDir(self, projectdir):
        if self.file:
            dir = projectdir + "/." + os.path.basename(self.file) + "/"
        else:
            dir = projectdir + "/" + self.getName() + "/"

        if os.path.isdir(dir):
            return dir

        if not(os.path.isfile(dir)):
            os.mkdir(dir)
            return dir

        # assertion has failed
        raise Exception("error in Track.assertDir: could not write to directory " + dir)


    
    def insertFile(self, file, override=False):
        if isVideoFile(file):
            if self.isAudioOnly():
                return
            clip = VideoFileClip(file)
        else:
            clip = AudioFileClip(file)
        setFilepath(clip, file)
        self.insertClip(clip, override=override)

    def insertClip(self, clip, filepath=None, override=False):
        if self.isLocked() and not(override):
            raise Exception("Track.insertClip: Track " + self.getName() + " is locked.")
        
        if self.isAudioOnly():
            if isVideoClip(clip):
                return None
        # else  video, currently allowwing all clips
        if self.empty():
            self.data = [clip]
            if isVideoClip(clip):
                # track size is clip size if it's the only and the first clip
                self.size = clip.size
                
                
            if isAudioClip(clip):
                self.audioOnly = True
            self.index = 1
            return
        self.data.insert(self.index, clip)
        self.right()
            
            
    def remove(self, override=False):
        if self.isLocked() and not(override):
            raise Exception("Track.remove: Track " + self.getName() + " is locked.")

        
        if (self.index is None) or (self.index >= len(self.data)):
            return
                         
        del self.data[self.index]
        #        self.left()
        if self.index >= len(self.data):
            self.index = len(self.data) - 1
        if self.empty():
            self.index = None
            return

        # make audio only if only audio remains
        if [] == list(filter(isVideoClip, self.data)):
            self.audioOnly = True
        
            
    def strIndex(self):
        if self.index is None:
            return "no clip"

        if self.atEnd():
            return "end of track"
        return "clip " + str(self.index)

    def isMergable(self):
        # a track is mergable if it's all video or all audio tracks. mixed tracks exist as containers and workspaces, like e.g. the graveyard track
        videos = list(filter(isVideoClip, self.data))
        audios = list(filter(isAudioClip, self.data))
        return not(videos and audios)


    def getDuration(self):
        return sum([clip.duration for clip in self.data])

    
    def recConcatenate(self, findFunc=lambda trackname, trackindex: []):
        if not(self.isMergable()):
            return None

        if self.empty():
            return None

        # we accumulate this tracks clips and child clips, setting start position according to offsets of subtracks. We do it like this because recursive calls to CompositeVideoClip etc are very inefficient
        (aclips, vclips) = ([], [])
        curStart = 0
        overlays = []
        suppressions = []
        for i in range(0, len(self.data)):
            #print("i: " + str(i))
            #print("fps " + str(self.data[i].fps))
            #print("audio fps " + str(self.data[i].audio.fps))            
            #print("curStart: " + str(curStart))
            if isAudioClip(self.data[i]):
                aclips.append(self.data[i].with_start(curStart))
            else:
                vclips.append(self.data[i].with_start(curStart))            
            children = findFunc(self, i)
            for childTrack in children:
                factor = childTrack.getParentAudioFactor()
                #print("childtrack " + childTrack.name[:5])
                #print("child fps " + str(childTrack.data[0].fps))                
                #print("factor " + str(factor))
                #print("offset " + str(childTrack.getOffset()))
                #print("duration " + str(childTrack.getDuration()))
                childstart = curStart+childTrack.getOffset()
                childend = curStart+childTrack.getOffset()+childTrack.getDuration()
                #print(str(childstart))
                #print(str(childend))                
                if not(factor is None):
                    #FIXME: assumming audio only
                    overlays += [clip.with_start(childstart) for clip in childTrack.data]
                    suppressions.append((factor, childstart, childend))
                elif childTrack.isAudioOnly():
                    aclips += [clip.with_start(childstart) for clip in childTrack.data]
                else:
                    vclips += [clip.with_start(childstart) for clip in childTrack.data]
                    

            curStart += self.data[i].duration

        if self.isAudioOnly():
            return CompositeAudioClip(aclips + [clip.audio for clip in vclips])
        # video track

        # size of clips
        if self.size:
            # we just brutalize the clips, if you want to preserve aspect ratio, the user has to resize them manually before
            resized_vclips = [clip.resize(new_size=self.size) for clip in vclips]
    

        video = CompositeVideoClip(resized_vclips)
        audio = CompositeAudioClip([video.audio] + aclips)
        for (factor, start, end) in suppressions:
            video = video.multiply_volume(factor, start_time=start, end_time=end)
            audio = audio.multiply_volume(factor, start_time=start, end_time=end)

        audio = CompositeAudioClip([audio] + overlays)
        video.audio = audio
        print("video fps " + str(video.fps))
        return video

    
    def concatenate(self, fade=False, clips=[]):
        if not(self.isMergable()):
            return None
        
        if self.empty():
            return None
            
        
        # quick job for audio tracks
        if self.isAudioOnly():
            resultClip = concatenate_audioclips(self.data)
        elif fade:
            # FIXME: no reason this shouldn't in principle work with audio only clips (except wonky library design in moviepy)
            t = self.fadeDuration
            c1 = self.data[0]
            c1.audio = c1.audio.audio_fadeout(t)
            c1 = c1.fadeout(t)
            acc = [c1]
            for clip in self.data[1:]:
#                acc.append(clip)#.crossfadein(2))
                cx = clip
                cx.audio = cx.audio.audio_fadein(t)
                cx.audio = cx.audio.audio_fadeout(t)
                cx = cx.fadein(t)
                cx = cx.fadeout(t)
                acc.append(cx)
                
            #            tmp = concatenate(acc, padding=-2,method="compose")
            resultClip = concatenate_videoclips(acc)
        else:
            resultClip = concatenate_videoclips(self.data)



    def clone(self):
        n = copy.copy(self)
        n.unlock()
        n.data = []
        for clip in self.data:
            n.data.append(clip.subclip(0))
        return n

            
            
