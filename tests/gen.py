#! /usr/bin/python3
import re
import sys
from collections import defaultdict
from awkpy_runtime import AwkpyRuntimeVarOwner, AwkpyRuntimeWrapper, AwkNext, AwkNextFile, AwkExit, AwkEmptyVar, AwkEmptyVarInstance
class AwkPyTranslated(AwkpyRuntimeWrapper):
    global AwkEmptyVarInstance
    def __init__(self):
        super().__init__()
        self._has_mainloop = True
        self.x=234
        self.z="power7"
    def MAINLOOP(self):
        if self._FLDS[1]=="Line.4":
            print(f'{self._FLDS[2]}')
runtime=AwkPyTranslated()
runtime._run(sys.argv)
