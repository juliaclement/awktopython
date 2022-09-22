#! /usr/bin/python3
re=__import__("re")
sys=__import__("sys")
collections=__import__("collections")
defaultdict=collections.defaultdict
awkpy_runtime=__import__("awkpy_runtime")
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
        self.y=AwkEmptyVarInstance
        self.w=AwkEmptyVarInstance
        self.z=AwkEmptyVarInstance
    def BEGIN(self):
        self.y="123456"
        self.w=-3
        self.z=self._substr(str(self.y),int(self.w))
        AwkpyRuntimeWrapper._ans=self.z
        raise AwkExit
runtime=AwkPyTranslated()
runtime._run(sys.argv[1:])
