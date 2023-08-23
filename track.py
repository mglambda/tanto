

from moviepy.editor import *

class Track(object):
    def __init__(self, file=None, name=None):
        self.file = file
        self.name = name
        self.data = []
        self.index = None
        self.fadeDuration = 1.0

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
        return self.name
            
    def empty(self):
        return len(self.data) == 0

    def get(self):
        if self.index is None:
            return None

        if self.index >= len(self.data):
            return None
        return self.data[self.index]
        


    def insertFile(self, file):
        clip = VideoFileClip(file)
        self.insertClip(clip)

    def insertClip(self, clip):
        if self.empty():
            self.data = [clip]
            self.index = 1
            return
        #        self.data = self.data[0:self.index] + [clip] + self.data[self.index+1:]
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

        if self.index >= len(self.data):
            return "new clip"
        return "clip " + str(self.index)

    def concatenate(self, fade=False):
        if self.empty():
            return None
    

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
