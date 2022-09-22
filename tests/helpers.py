#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
""" AWK - Python translator tests
    basic functionality """ 
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

# ***** Even though the generated code has "import re", if we
# ***** don't import it here also the execed code can't find it
# ***** the same doesn't apply to all the awkpy_runtime.py library,
# ***** AwkNextFile we need AwkpyRuntimeWrapper we don't.
# ***** Go figure
import pytest
import re
import random
import math
import sys
from pathlib import Path
from collections import defaultdict
try:
    from awkpy import run
except:
    path=Path(__file__).parent.parent/'code'
    sys.path.append(str(path))
    from awkpy import run
from awkpy_args import AwkPyArgParser
from awkpy_compiler import AwkPyCompiler
from awkpy_runtime import AwkEmptyVar,AwkEmptyVarInstance,AwkNextFile,AwkExit,AwkpyRuntimeWrapper,AwkpyRuntimeVarOwner

class Fuzzy():
    def __init__(self, target:float, max_err:float):
        self.target = target
        self.max_err=max_err
    def __eq__(self, o) -> bool:
        if (self.target-self.max_err) > o:
            return False
        if o > (self.target + self.max_err):
            return False
        return True

# unless specified otherwise, test input files are in the same directory as 
# the tests
def full_file_name(test_file):
    return str(Path(__file__).parent / test_file)

empty_txt = full_file_name('empty.txt')

# we expect to find the file empty.txt in the same directory

def compile_run( awk: str, files:list = [empty_txt]):
    compiler=AwkPyCompiler(debug=False)
    python_source=compiler.compile(awk)
    argv=["prog"]+files
    python_source+=f'\nrt=AwkPyTranslated()\nrt._run({argv})'
    code=compile(python_source,'generated','exec')
    exec(code)
    return AwkpyRuntimeWrapper._ans

def compile_run_capsys_assert( capsys, expected:str, awk: str, files:list = [empty_txt]):
    compile_run( awk, files)
    captured = capsys.readouterr()
    assert captured.out == expected

def compile_run_answer_assert(expected, awk: str, files:list = [empty_txt]):
    args=["program"]
    if awk is not None:
        args.append(awk)
    args.extend(files)
    ans=run(args)
    assert ans == expected

def check_arg_parser(value, check, args:list):
    compiler_options=[]
    runtime_options=[]
    variables=[]
    parser=AwkPyArgParser(compiler_options,runtime_options,variables)
    args.insert(0,"program")
    parser.parse(args)
    field=check(parser,compiler_options,runtime_options,variables)
    assert field==value

if __name__=="__main__":
    compile_run_answer_assert(0,None, ["-e","{print $1,$2,$3;}","lines.txt"])
    print('.')
