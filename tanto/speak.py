from subprocess import Popen, PIPE
import sys, platform

class Speaker(object):
    def __init__(self, rate=None, punct="some", volume=None, engine=None):
        """Creates a new tts speaker object. Rate, volume etc. will be passed onto the underlying tts engine. Engine can be set to "spd-say", "espeak", etc. Leave at None to select a platform appropriate option automatically."""
        self._rate = rate
        self._punct = punct
        self._volume = volume
        self._engine = None
        self._p = None
        self.init(engine)
        
    def init(self, engine=None):
        id = platform.system()
        if id == "Linux":
            # we it's 2024 for christ's sake, will use native spd-say
            self._engine = "spd-say"
            self._rate = 40 if self._rate is None else self._rate
            self._volume = 0.7 if self._volume is None else self._volume
        elif id == "Darwin":
            # mac os
            self._engine = "say"
            self._rate = 150 if self._rate is None else self._rate
            self._volume = 100 if self._volume is None else self._volume
        elif id == "Windows":
            # FIXME: look into sapi5
            self._engine = "espeak"
            self._rate = 150 if self._rate is None else self._rate
            self._volume = 100 if self._volume is None else self._volume
        else:
            # here be dragons
            raise RuntimeError("Sorry, TTS on your platform is not supported.")
        
    def speak(self, w):
        if (w is None) or (w == ""):
            return

        if self._engine == "espeak":
            if self._p:
                self._p.terminate()
            self._p = Popen(["espeak", "-a", str(self._volume), "-s", str(self._rate),w])
        elif self._engine == "spd-say":
            self._p = Popen(["spd-say", "-m", self._punct, "-r", str(self._rate), w], stdin=PIPE)
        elif self._engine == "say":
            if self._p:
                self._p.terminate()            
            # weirdly mac doesn't support volume
            self._p = Popen(["say", "-r", self._rate,w])
        else:
            raise RuntimeError("Selected TTS engine " + self._engine + " is not supported.")
