
import os, glob
from moviepy.editor import *
from tanto_utility import *
import copy

class Track(object):

    storable = "parent parentAudioFactor audioOnly index offset locked workspacePreference".split(" ")
    def __init__(self, file=None, name=None, audioOnly=False, locked=False, parent=None, offset=0, workspacePreference=1, temporary=True, parentAudioFactor=None):
        self.file = file
        self.dir = dir
        self.temporary = temporary
        self.parentAudioFactor = parentAudioFactor
        self.workspacePreference = workspacePreference
        self.locked = locked
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

    def getParentTrackName(self):
        if self.parent is None:
            return None
        return self.parent[0]

    def getParentTrackIndex(self):
        if self.parent is None:
            return None
        return self.parent[1]

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
        w = self.getName()[:30]

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
        if self.file:
            return
        
        dir = self.assertDir(projectdir)
        for key in Track.storable:
            filename = "." + key
            f = open(dir + "/" + filename, "w")
            f.write(str(self.__dict__[key]))
            f.close()
                             

                 
            
            
    
    def save(self, projectdir):
        if self.file:
            return

        self.temporary = False
        self.storeVars(projectdir)
        dir = self.assertDir(projectdir)
        for i in range(len(self.data)):
            clip = self.data[i]
            # clip has no origin, was probably created during program execution
            if isVideoClip(clip):
                writeClip(clip, dir + str(i) + ".mkv")
            else:
                writeClip(clip, dir + str(i) + ".wav")

                
    def assertDir(self, projectdir):
        dir = projectdir + "/" + self.getName() + "/"


        if os.path.isdir(dir):
            return dir

        if not(os.path.isfile(dir)):
            os.mkdir(dir)
            return dir

        # try something nasty
        self.dir = dir + "_"
        return self.assertDir()
        
        
    
    
                    
                    

    
                
                
                
                
            

            




            
            

        

    def insertFile(self, file):
        if isVideoFile(file):
            if self.isAudioOnly():
                return
            clip = VideoFileClip(file)
        else:
            clip = AudioFileClip(file)
        setFilepath(clip, file)
        self.insertClip(clip)

    def insertClip(self, clip, filepath=None):
        if self.isAudioOnly():
            if isVideoClip(clip):
                return None
        # else  video, currently allowwing all clips
        if self.empty():
            self.data = [clip]
            if isAudioClip(clip):
                self.audioOnly = True
            self.index = 1
            return
        self.data.insert(self.index, clip)
        self.right()
            
            
    def remove(self):
        if (self.index is None) or (self.index >= len(self.data)):
            return
                         
        del self.data[self.index]
        self.left()
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

    
    def recConcatenate2(self, findFunc=lambda trackname, trackindex: []):
        if not(self.isMergable()):
            return None

        if self.empty():
            return None

        # we accumulate this tracks clips and child clips, setting start position according to offsets of subtracks. We do it like this because recursive calls to CompositeVideoClip etc are very inefficient
        (aclips, vclips) = ([], [])
        curStart = 0
        for i in range(0, len(self.data)):
            print("i: " + str(i))
            print("fps " + str(self.data[i].fps))
            print("curStart: " + str(curStart))
            if isAudioClip(self.data[i]):
                aclips.append(self.data[i].with_start(curStart))
            else:
                vclips.append(self.data[i].with_start(curStart))            
            children = findFunc(self, i)
            for childTrack in children:
                factor = childTrack.getParentAudioFactor()
                print("childtrack " + childTrack.name[:5])
                print("factor " + str(factor))
                print("offset " + str(childTrack.getOffset()))
                print("duration " + str(childTrack.getDuration()))
                if not(factor is None):
                    aclips = [clip.multiply_volume(factor, start_time=curStart+childTrack.getOffset(), end_time=curStart+childTrack.getOffset()+childTrack.getDuration()) for clip in aclips]
                    vclips = [clip.multiply_volume(factor, start_time=curStart+childTrack.getOffset(), end_time=curStart+childTrack.getOffset()+childTrack.getDuration()) for clip in vclips]
                    
                if childTrack.isAudioOnly():
                    aclips += [clip.with_start(curStart + childTrack.getOffset()) for clip in childTrack.data]
                else:
                    vclips += [clip.with_start(curStart + childTrack.getOffset()) for clip in childTrack.data]
                    

            curStart += self.data[i].duration

        if self.isAudioOnly():
            return CompositeAudioClip(aclips + [clip.audio for clip in vclips])
        # video track
        video = CompositeVideoClip(vclips)
        audio = CompositeAudioClip([video.audio] + aclips)
        video.audio = audio
        return video

    
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
            print("i: " + str(i))
            print("fps " + str(self.data[i].fps))
            print("audio fps " + str(self.data[i].audio.fps))            
            print("curStart: " + str(curStart))
            if isAudioClip(self.data[i]):
                aclips.append(self.data[i].with_start(curStart))
            else:
                vclips.append(self.data[i].with_start(curStart))            
            children = findFunc(self, i)
            for childTrack in children:
                factor = childTrack.getParentAudioFactor()
                print("childtrack " + childTrack.name[:5])
                print("child fps " + str(childTrack.data[0].fps))                
                print("factor " + str(factor))
                print("offset " + str(childTrack.getOffset()))
                print("duration " + str(childTrack.getDuration()))
                childstart = curStart+childTrack.getOffset()
                childend = curStart+childTrack.getOffset()+childTrack.getDuration()
                print(str(childstart))
                print(str(childend))                
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
#        for (factor, start, end) in suppressions:
#            vclips = [clip.multiply_volume(factor, start, end) for clip in vclips]
#            aclips = [clip.multiply_volume(factor, start, end) for clip in aclips]
            
        video = CompositeVideoClip(vclips)
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
        n.data = []
        for clip in self.data:
            n.data.append(clip.subclip(0))
        return n

            
            
