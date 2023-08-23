

from moviepy.editor import *

class Track(object):
    def __init__(self, file=None, name=None):
        self.file = file
        self.name = name
        self.data = []
        self.index = None

    def right(self):
        if self.index is None:
            return
        
        if self.index+1 < len(self.data):
            self.index += 1

    def left(self):
        if self.index is None:
            return
        
        if self.index-1 >= 0:
            self.index -= 1

    def getName(self):
        return self.name
            
    def empty(self):
        return self.index is None

    def get(self):
        if self.index is None:
            return None
        
        return self.data[self.index]

    def insertFile(self, file):
        clip = VideoFileClip(file)
        self.insertClip(clip)

    def insertClip(self, clip):
        if self.empty():
            self.data = [clip]
            self.index = 0
            return
        #        self.data = self.data[0:self.index] + [clip] + self.data[self.index+1:]
        self.data.insert(self.index, clip)
        self.right()
            
            
    
