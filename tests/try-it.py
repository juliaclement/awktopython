#import re
#from awkpy_runtime import AwkpyRuntimeWrapper,AwkpyRuntimeVarOwner,AwkNext,AwkNextFile,AwkExit,AwkEmptyVar,AwkEmptyVarInstance
# import importlib
#AwkEmptyVarInstance = awkpy_runtime.AwkEmptyVarInstance
python_source='''
awkpy_runtime=__import__('awkpy_runtime')
AwkpyRuntimeWrapper = awkpy_runtime.AwkpyRuntimeWrapper
AwkEmptyVarInstance = awkpy_runtime.AwkEmptyVarInstance
class AwkPyTranslated(AwkpyRuntimeWrapper):
    global AwkEmptyVarInstance
    def __init__(self):
        super().__init__()
        self.ABC="DEF"
        self.x=AwkEmptyVarInstance
        self.y={}
        self.a=AwkEmptyVarInstance
    def BEGIN(self):
        print(f'{self.ABC}')
        self.x="123./456..789.101112"
        self.y = self._to_array(str(self.x).split("./"))
        for self.a in self.y:
            print(f'{self.a} {self.y.get(self.a,"")}')
            AwkpyRuntimeWrapper._ans=self.y[self.a]
        print(f'Qrp')
rt=AwkPyTranslated()
argv=["prog"]
rt._run(argv)'''

code=compile(python_source,'generated','exec')
exec(code)
print( "x" )
awkpy_runtime=__import__('awkpy_runtime')
AwkpyRuntimeWrapper = awkpy_runtime.AwkpyRuntimeWrapper
print( AwkpyRuntimeWrapper._ans)