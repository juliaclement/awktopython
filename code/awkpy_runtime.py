#!/usr/bin/python3
"""
    Runtime library for the awk to python translator.
"""
#
# Copyright (C) 2022 Julia Ingleby Clement
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from collections import defaultdict
import sys
import re
import subprocess
import os
from pathlib import Path
from awkpy_args import AwkPyArgParser

exit_code = 0
class AwkExit(Exception):
    pass
class AwkNext(Exception):
    pass
class AwkNextFile(Exception):
    pass
class AwkEmptyVar():
    """
    AWK permits a=x+1 and y=x ".tail" when x has not been initialised.
    Python doesn't, nor does it seem to have a built-in type that permits 
    it to be treated as both empty string & 0.
    This class might help in simple cases
    """
    def __bool__(self) -> bool:
        return False
    def __int__(self) -> int:
        return 0
    def __float__(self) -> float:
        return 0.0
    def __str__(self) -> str:
        return ""
    def __repr__(self) -> str:
        return "AwkEmptyVar()"
    def __neg__(self) -> int:
        return 0
    def __pos__(self) -> int:
        return 0
    def __abs__(self) -> int:
        return 0
    def __invert__(self) -> int:
        return ~0
    def __eq__(self, anotherObj)->bool:
        if isinstance( anotherObj, str ):
            return anotherObj == ""
        return int(anotherObj) == 0
    def __add__(self, anotherObj):
        return anotherObj
    def __sub__(self, anotherObj):
        return - anotherObj
    def __mul__(self, anotherObj):
        return 0
    def __truediv__(self, anotherObj) -> int:
        return 0
    def __floordiv__(self, anotherObj) -> int:
        return 0
    def __mod__(self, anotherObj) -> int:
        return 0
    def __pow__(self, anotherObj, modulo=None):
        return 0
    def __iadd__(self, anotherObj) -> int:
        return anotherObj
    def __isub__(self, anotherObj) -> int:
        return -anotherObj
    def __imul__(self, anotherObj) -> int:
        return 0
    def __itruediv__(self, anotherObj) -> int:
        return 0
    def __ifloordiv__(self, anotherObj) -> int:
        return 0
    def __imod__(self, anotherObj) -> int:
        return 0
    def __ipow__(self, anotherObj, modulo=None) -> int:
        return 0
    def __ilshift__(self, anotherObj) -> int:
        return 0
    def __irshift__(self, anotherObj) -> int:
        return 0
    def __iand__(self, anotherObj) -> int:
        return 0
    def __ixor__(self, anotherObj) -> int:
        return anotherObj
    def __ior__(self, anotherObj) -> int:
        return anotherObj
    """ These methods are called to implement the binary arithmetic operations (+, -, *, @, /, //, %,
        divmod(), pow(), **, <<, >>, &, ^, |) with reflected (swapped) operands.
        from https://docs.python.org/3/reference/datamodel.html
        For example while AwkEmptyVar + 7 calls __add__, 7 + AwkEmptyVar should call __radd__
    """
    def __radd__(self, anotherObj):
        return anotherObj
    def __rsub__(self, anotherObj):
        return anotherObj
    def __rmul__(self, anotherObj):
        return 0
    # def __rmatmul__(self, anotherObj):
    #    return 0
    def __rtruediv__(self, anotherObj):
        raise ZeroDivisionError # anotherObj / 0
    def __rfloordiv__(self, anotherObj):
        raise ZeroDivisionError # anotherObj // 0
    def __rmod__(self, anotherObj):
        raise ZeroDivisionError # anotherObj % 0
    """
    # I don't think there is an AWK construct that will generate a divmod call
    # so, I've omitted them
    def __divmod__(self, anotherObj):
        return (0,0)
    def __rdivmod__(self, anotherObj):
        raise ZeroDivisionError
    """
    def __rpow__(self, anotherObj, modulo=None):
        return 1
    def __rlshift__(self, anotherObj):
        return anotherObj
    def __rrshift__(self, anotherObj):
        return anotherObj
    def __rand__(self, anotherObj):
        return 0
    def __rxor__(self, anotherObj):
        return anotherObj
    def __ror__(self, anotherObj):
        return anotherObj

    the_instance=None
    @classmethod
    def instance(cls):
        return cls.the_instance

AwkEmptyVar.the_instance=AwkEmptyVar()
AwkEmptyVarInstance=AwkEmptyVar.instance()

class AwkpyRuntimeVarOwner():
    global AwkEmptyVarInstance
    """A class to support translations of AWK variable manipulations
       such as  ++, -- that are not found in Python.
       Used as the base class of AwkpyRuntimeWrapper and directly for 
       owning local variables in translated functions
    """
    def _pre_inc_var(self, varname):
        """self._pre_inc_var('x') implements ++x"""
        try:
            value=getattr(self,varname)
        except:
            value=0
        value+=1
        setattr(self,varname,value)
        return value
    def _post_inc_var(self, varname):
        """self._post_inc_var('x') implements x++"""
        try:
            value=getattr(self,varname)
        except:
            value=AwkEmptyVarInstance
        setattr(self,varname,value+1)
        return value
    def _pre_dec_var(self, varname):
        """self._pre_dec_var('x') implements --x"""
        try:
            value=getattr(self,varname)
        except:
            value=0
        value-=1
        setattr(self,varname,value)
        return value
    def _post_dec_var(self, varname):
        """self._post_dec_var('x') implements x--"""
        try:
            value=getattr(self,varname)
        except:
            value=AwkEmptyVarInstance
        setattr(self,varname,value-1)
        return value
    """ As self is never used, the array element versions don't
        need to be in the class.
        I have just placed them here for convenience
    """
    def _pre_inc_arr(self, array:dict, key):
        """self._pre_inc_arr(array,x) implements ++array[x]"""
        value=array.get(key,0) # AWK doc says this should be an empty string, AwkEmptyVarInstance?
        value+=1
        array[key]=value
        return value
    def _pre_dec_arr(self, array:dict, key):
        """self._pre_dec_arr(array,x) implements --array[x]"""
        value=array.get(key,0) # AWK doc says this should be an empty string, AwkEmptyVarInstance?
        value-=1
        array[key]=value
        return value
    def _post_inc_arr(self, array:dict, key):
        """self._post_inc_arr(array,x) implements array[x]++"""
        value=array.get(key,AwkEmptyVarInstance) # AWK doc says this should be an empty string but that can then be treated as 0
        array[key]=value+1
        return value
    def _post_dec_arr(self, array:dict, key):
        """self._pre_dec_arr(array,x) implements --array[x]"""
        value=array.get(key,0) # AWK doc says this should be an empty string AwkEmptyVarInstance?
        value=array.get(key,AwkEmptyVarInstance) # AWK doc says this should be an empty string but that can then be treated as 0
        array[key]=value-1
        return value
    def _substr(self, string:str, start:int, length:int=None) -> str:
        if start<1:
            start=1
        elif start > len(string):
            return ''
        start -= 1 # AWK uses 1 based, Python 0 based
        if length is None:
            return string[start:]
        end=min(start+length,len(string))
        return string[start:end]

    def _to_array(self,list,offset=1):
        """Python has lists & dicts. AWK only has dict like Arrays"""
        ans=defaultdict(AwkEmptyVar)
        for i in range(len(list)):
            ans[i+offset] = list[i]
        return ans

    def __init__(self):
        pass

class AwkpyRuntimeWrapper(AwkpyRuntimeVarOwner):
    _ans=0
    def BEGIN(self):
        """
            This method is run before the file input begins.
            It can be used to initialise variables, etc
        """
        pass
    def BEGINFILE(self):
        """
            This method is run before each file's input begins.
            It can be used to initialise variables, etc per-file 
        """
        pass
    def MAINLOOP(self):
        """
            This method is run once for each input line.
            Typically where most of the processing occurs
        """
        pass
    def ENDFILE(self):
        """
            This method is run after each file's input ends.
            Typically used for any clean-up and printing per-file summaries.
        """
        pass
    def END(self):
        """
            This method is run after all file input ends.
            Typically used for any clean-up and printing summaries.
        """
        pass
    def _get_stdin(self):
            self.FNR=0
            self.FILENAME = '-'
            self._FLDS=[]
            self.NF=0
            self._nextfile = False
            self.BEGINFILE()
            yield from sys.stdin
            self.ENDFILE()

    def _var_on_commandline(self,opt,arg):
        '''implements command line [-v] var=val '''
        optn=opt.split('=',1)
        setvar=optn[0]
        val=optn[1]
        # gawk accepts -v namespace::name=whatever.
        # we havent yet implemented namespaces, but should support
        # the default "awk::" namespace
        if '::' in setvar:
            optn=setvar.split('::',1)
            namespace=optn[0]
            setvar = optn[1]
            if namespace != 'awk':
                print(f"{arg}: Namespaces not implemented yet")
                exit(1)
        # HEURISTIC: if the value is a number, convert it to one
        # Damned if I know if this is the correct thing to do
        # it duplicates what we do in the compiler so if we change
        # one we should change both.
        try:
            value=float(val)
        except:
            value=val
        setattr(self, setvar, value)

    def _get_lines(self):
        """
        Generator to return input lines while managing record counts
        """
        if(self.ARGC<1):
            yield from self._get_stdin()
        else:
            for name in self.ARGV:
                if name[0].isalpha() and '=' in name:
                    self._var_on_commandline(name,name)
                else:
                    self.FILENAME = name
                    self._nextfile=False
                    self.FNR=0
                    if self.FILENAME=='-':
                        yield from self._get_stdin()
                    else:
                        self._FLDS=[]
                        self.NF=0
                        self.BEGINFILE()
                        with open(self.FILENAME) as current_file:
                            yield from current_file
                        self.ENDFILE()
    def _run(self,argv):
        options=[]
        variables=[]
        parser=AwkPyArgParser(options,self.ARGV,variables)
        parser.code_found = True # We are the run-time, not the compiler
        parser.parse(argv)
        for v in variables:
            optn=v[2:]
            self._var_on_commandline(optn,v)
        self.ARGC=len(self.ARGV)
        AwkpyRuntimeWrapper._ans = 0
        try:
            self.BEGIN()
            if self._has_mainloop: # only process files and run mainloop if it has some statements
                for line in self._get_lines():
                    # Can't find how to advance to the next file in the generator
                    # so just consume lines. YUCK!
                    # Possible solution https://stackoverflow.com/questions/3164785/stop-generator-from-within-block-in-python
                    if self._nextfile:
                        continue
                    if self.FS in [' ','']:
                        line=line.strip(' \t\n\r')
                        FLDS=line.split()
                    else:
                        line=line.strip('\n\r')
                        FLDS=line.split(self.FS)
                    self.NF=len(FLDS)
                    FLDS.insert(0,line)
                    self._FLDS=self._to_array(FLDS,0)
                    self.NR += 1
                    self.FNR += 1
                    try:
                        self.MAINLOOP()
                    except AwkNext:
                        pass
                    except AwkNextFile:
                        self._nextfile = True
        except AwkExit:
            pass
        try:
            self.END()
        except AwkExit:
            pass
        set_exit_code( AwkpyRuntimeWrapper._ans )
        return AwkpyRuntimeWrapper._ans
    def __init__(self):
        super().__init__()
        self.NR = 0
        self.FNR = 0
        self.NF = 0
        self.FS = ' '
        self.OFS='\t'
        self.ARGC=0
        self.ARGV=[]
        self._nextfile=False
        # if no statements are present in the main loop, 
        # input files are not processed
        self._has_mainloop=False
def set_exit_code(code):
    global exit_code
    exit_code = code