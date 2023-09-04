from queue import Queue
import threading
import sounddevice as sd
import soundfile as sf
import numpy  
from tempfile import mktemp


class AudioRecorder(object):
    def __init__(self, samplerate=44100, channels=2):
        self.samplerate = samplerate
        self.channels = channels
        self._init()
        
        


    def _init(self):
        self.status = None
        self.flag = threading.Event()
        self.data = Queue()
        self.file = mktemp(suffix=".wav")        



    def _worker(self):
        with sf.SoundFile(self.file,
                          mode='x',
                          #subtype=??, 
                          samplerate=self.samplerate,
                          channels=self.channels) as file:
            with sd.InputStream(samplerate=self.samplerate,
                                #device=???,
                            channels=self.channels,
                                callback=self._callback):        
                while self.flag.isSet():
                    file.write(self.data.get())

    def _callback(self, indata, frames, time, status):
        self.status = status
        self.data.put(indata.copy())        

    def getStatus(self):
        return self.status

    def isRecording(self):
        return self.flag.isSet()

    def wait(self):
        self.flag.wait()
        
    def start(self):
        if self.isRecording():
            return False
        
        self._init()
        self.flag.set()
        t = threading.Thread(target=self._worker)
        t.start()
        return True
    

    def stop(self):
        if not(self.isRecording()):
            return None
        
        self.flag.clear()
        return self.file
        
        
        
        
