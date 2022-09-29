#!/usr/bin/python3
"""
    AWK to python translator: 
    Classes common between awkpy.py and awkpycc.py
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

from sys import argv


class AwkPyArgParser:
    '''Parses commandline args.

        Walks sys.args processing them & distributing
        between args that "belong" to the compiler 
        and those which "belong" to the runtime.
    '''

    def __init__(self, compiler_options: list, runtime_options: list, variables: list):
        self.compiler_options = compiler_options
        self.runtime_options = runtime_options
        self.variables = variables
        self.debug = False
        self.code_found = False
        self.output_file_name = None
        self.program_name = "generated"


    def parse(self, args=argv):
        self.program_name = args[0]
        i = 1  # skip program name
        while i < len(args):
            curr_arg = args[i]
            if curr_arg[0] == "-" and len(curr_arg) > 1:
                if curr_arg[1] == "-":  # end of arguments, data files follow
                    i += 1
                    self.runtime_options.extend(args[i:])
                    break
                if curr_arg[1] == "d":  # self.debug
                    self.debug = True
                    print(args)
                elif curr_arg[1] == "e":  # source text
                    self.code_found = True
                    if len(curr_arg) == 2:
                        i += 1
                        self.compiler_options.append("-e" + args[i])
                    else:
                        self.compiler_options.append(curr_arg)
                # -i is very similar to -f merge them for now.
                elif curr_arg[1] in "if":  # source file, include file
                    if len(curr_arg) == 2:
                        i += 1
                        self.compiler_options.append(f"{curr_arg}{args[i]}")
                    else:
                        self.compiler_options.append(curr_arg)
                elif curr_arg[1] == "o":  # Python source file output
                    if len(curr_arg) == 2:
                        i += 1
                        self.output_file_name = args[i]
                    else:
                        self.output_file_name = curr_arg[2:]
                elif curr_arg[1] == "F":  # set variable FS
                    if len(curr_arg) == 2:
                        i += 1
                        self.variables.append("-vFS=" + args[i])
                    else:
                        curr_arg=curr_arg[2:]
                        self.variables.append('-vFS=' + curr_arg)
                elif curr_arg[1] == "v":  # set variable
                    if len(curr_arg) == 2:
                        i += 1
                        self.variables.append("-v" + args[i])
                    else:
                        self.variables.append(curr_arg)
                elif (
                    curr_arg[1:] == "Wr"
                ):  # all remaining args sent to runtime skipping compiler
                    self.runtime_options.extend(args[i:])
                    break
            else:  # input file or AWK program
                if self.code_found:
                    self.runtime_options.extend(args[i:])
                    break
                else:
                    self.compiler_options.append("-e" + curr_arg)
                    self.code_found = True
            i += 1


def _format_g(raw_value)->str:
    value=float(raw_value)
    sci_str = f'{value:e}'
    float_str = f'{value}'
    return sci_str if len(sci_str) < len(float_str) else float_str


class AwkPySprintfConversion():
    '''List of printf/sprintf conversion commands'''
    def __init__(self,char,static,dynamic,default_precision='',format_sfx=''):
        self.char = char
        self.static = static
        self.dynamic = dynamic
        self.default_precision = default_precision
        self.format_sfx = format_sfx

'''All conversion specifiers in the POSIX printf families.
    n & p are tagged as omitted as they are in the POSIX C
    standard but not in the AWK one, in any case n is
    regarded as unsafe, & p is highly unlikely to be useful '''
AwkPySprintfConversion.all_conversions={
    'a' : AwkPySprintfConversion('a', 'hex(float({}))[2:]',  lambda v: hex(float(v))[2:] ),
    'A' : AwkPySprintfConversion('A', 'hex(float{}))[2:].upper()',  lambda v: hex(float(v))[2:].upper() ),
    'c' : AwkPySprintfConversion('c', 'char({})',  lambda v: str(v)[0] ),
    'd' : AwkPySprintfConversion('d', 'int({})',  lambda v: int(v) ),
    'e' : AwkPySprintfConversion('e', 'float({})',  lambda v: float(v),default_precision='6', format_sfx='e' ),
    'E' : AwkPySprintfConversion('E', 'float({})',  lambda v: float(v),default_precision='6', format_sfx='E' ),
    'f' : AwkPySprintfConversion('f', 'float({})',  lambda v: float(v),default_precision='6', format_sfx='f' ),
    'F' : AwkPySprintfConversion('F', 'float({})',  lambda v: float(v),default_precision='6', format_sfx='F' ),
    'g' : AwkPySprintfConversion('g', 'self._format_g({})',  lambda v: _format_g(v) ),
    'G' : AwkPySprintfConversion('G', 'self._format_g({}).upper()',  lambda v: _format_g(v).upper() ),
    'i' : AwkPySprintfConversion('i', 'int({})',  lambda v: int(v) ),
    # unsafe 'n' : AwkPySprintfConversion('n', '',  lambda v: v ),
    'o' : AwkPySprintfConversion('o', 'oct({})[2:]',  lambda v: oct(v)[2:] ),
    # omitted 'p' : AwkPySprintfConversion('p', '',  lambda v: v ),
    's' : AwkPySprintfConversion('s', 'str({})',  lambda v: str(v) ),
    'u' : AwkPySprintfConversion('u', 'int({})',  lambda v: int(v) ),
    'x' : AwkPySprintfConversion('x', 'hex(int({}))[2:]',  lambda v: hex(int(v))[2:] ),
    'X' : AwkPySprintfConversion('X', 'hex(int({}))[2:].upper()',  lambda v: hex(int(v))[2:].upper() ),
}