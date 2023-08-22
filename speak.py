#!/bin/python3

from subprocess import Popen, PIPE
import sys

class Speaker(object):
    def __init__(self, speed=50):
        self._speed = speed
        self.init()
        

    def init(self):
#        self._espeak = Popen(["espeak-ng", "-s " + str(self._speed), "--"], stdin=PIPE)
        return


    def speak(self, w):
        Popen(["spd-say", "-r " + str(self._speed), w], stdin=PIPE)
        
#    def speak(self, w):
##        self._espeak.communicate(input=bytes(w, sys.getdefaultencoding()))
#        self.init()
#        self._espeak.stdin.write(bytes(w+ "\n", sys.getdefaultencoding()))
#        self._espeak.stdin.flush()
