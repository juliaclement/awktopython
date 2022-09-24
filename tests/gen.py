#! /usr/bin/python3
re=__import__("re")
sys=__import__("sys")
collections=__import__("collections")
defaultdict=collections.defaultdict
from pathlib import Path
try:
    import awkpy_runtime
except:
    path=Path(__file__).parent.parent/'code'
    sys.path.append(str(path))
    import awkpy_runtime
AwkpyRuntimeVarOwner=awkpy_runtime.AwkpyRuntimeVarOwner
AwkpyRuntimeWrapper=awkpy_runtime.AwkpyRuntimeWrapper
AwkNext=awkpy_runtime.AwkNext
AwkNextFile=awkpy_runtime.AwkNextFile
AwkExit=awkpy_runtime.AwkExit
AwkEmptyVar=awkpy_runtime.AwkEmptyVar
AwkEmptyVarInstance=awkpy_runtime.AwkEmptyVarInstance
class AwkPyTranslated(AwkpyRuntimeWrapper):
    global AwkEmptyVarInstance
    def __init__(self):
        super().__init__()
        self.l=AwkEmptyVarInstance
        self.r=AwkEmptyVarInstance
    def END(self):
        self.OFS="-"
        self.l="left"
        self.r="right"
        print(f'{self.l}{self.OFS}{self.r}')
runtime=AwkPyTranslated()
runtime._run(sys.argv)