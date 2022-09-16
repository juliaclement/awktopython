#!/usr/bin/python3
"""
    AWK to python translator: parse commandline args.

    Walks sys.args processing them & distributing
    between args that "belong" to the compiler 
    and those which "belong" to the runtime.

    Common between awkpy.py and awkpycc.py
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

class AwkPyArgParser():
    def __init__(self,compiler_options:list,runtime_options:list,variables:list):
        self.compiler_options = compiler_options
        self.runtime_options = runtime_options
        self.variables = variables
        self.debug=False
        self.code_found=False
        self.output_file_name=None
        self.program_name="generated"
    def parse(self,args=argv):
        self.program_name=args[0]
        i=1 # skip program name
        while i < len(args):
            curr_arg=args[i]
            if curr_arg[0]=='-' and len(curr_arg)>1:
                if curr_arg[1] == '-': # end of arguments, data files follow
                    i+=1
                    self.runtime_options.extend(args[i:])
                    break
                if curr_arg[1] == 'd': # self.debug
                    self.debug=True
                    print(args)
                elif curr_arg[1] == 'e': # source text
                    self.code_found=True
                    if len(curr_arg) == 2:
                        i+=1
                        self.compiler_options.append('-e'+args[i])
                    else:
                        self.compiler_options.append(curr_arg)
                # -i is very similar to -f merge them for now.
                elif curr_arg[1] in 'if': # source file, include file
                    if len(curr_arg) == 2:
                        i+=1
                        self.compiler_options.append('-f'+args[i])
                    else:
                        self.compiler_options.append(curr_arg)
                elif curr_arg[1] == 'o': # Python source file output
                    if len(curr_arg) == 2:
                        i+=1
                        self.output_file_name=args[i]
                    else:
                        self.output_file_name=curr_arg[2:]
                elif curr_arg[1] == 'v': # set variable
                    if len(curr_arg) == 2:
                        i+=1
                        self.variables.append('-v'+args[i])
                    else:
                        self.variables.append(curr_arg)
                elif curr_arg[1:] == 'Wr': # all remaining args sent to runtime skipping compiler
                    self.runtime_options.extend(args[i:])
                    break
            else: # input file or AWK program
                if self.code_found:
                    self.runtime_options.extend(args[i:])
                    break
                else:
                    self.compiler_options.append('-e'+curr_arg)
                    self.code_found = True
            i+=1