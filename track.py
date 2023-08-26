
import os, glob
from moviepy.editor import *
from tanto_utility import *
import copy

class Track(object):
    def __init__(self, file=None, name=None, audioOnly=False):
        self.file = file
        self.dir = dir
        self.name = name
        self.audioOnly = audioOnly
        self.data = []
        self.index = None
        self.fadeDuration = 1.0

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


    def getName(self):
        if self.isAudioOnly():
            return self.name + "-audio"
        return self.name
            
    def empty(self):
        return len(self.data) == 0

    def get(self):
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
        print(filepath)
        #        files = glob.glob(filepath + "/*")
        files = os.listdir(filepath)
        print(len(files))
        track = Track(name=trackNameFromFile(filepath))        
        for filename in files:
            file = filepath + "/" + filename
            print(file)
            if os.path.isdir(file):
                continue
            track.insertFile(file)

        if len(list(filter(isAudioClip, track.data))) == len(track.data):
            track.audioOnly = True
        return track

    def save(self, projectdir):
        if self.file:
            return
        
        for i in range(len(self.data)):
            clip = self.data[i]
            # clip has no origin, was probably created during program execution
            dir = self.assertDir(projectdir)
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

        print(str(self.index))
        print(str(len(self.data)))              

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
    
    def concatenate(self, fade=False):
        if not(self.isMergable()):
            return
        
        if self.empty():
            return None

        # quick job for audio tracks
        if self.isAudioOnly():
            return concatenate_audioclips(self.data)

        if fade:
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
            tmp = concatenate_videoclips(acc)
        else:
            tmp = concatenate_videoclips(self.data)

        # there's a bug in moviepy with audio fps, so we have to workaround        
        x = self.data[0].audio
        tmp.audio.fps = x.fps
        return tmp


    def clone(self):
        n = copy.copy(self)
        n.data = []
        for clip in self.data:
            n.data.append(clip.subclip(0))
        return n

            
            
