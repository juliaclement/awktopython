#!/usr/bin/python3
"""
    AWK to python translator: compile and save to disk.
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
import sys
import os
from awkpy_compiler import AwkPyCompiler
from awkpy_args import AwkPyArgParser
#----
def run(args):
    compiler=AwkPyCompiler(compile_to_disk=True, debug=False)
    compiler_args=[]
    runtime_args=[]
    arg_parser=AwkPyArgParser(compiler_args,runtime_args,compiler_args)
    arg_parser.parse(args)
    compiler.do_debug = arg_parser.debug
    python_source=compiler.compile(compiler_args)+'\nruntime=AwkPyTranslated()\nruntime._run(sys.argv)\n'
    if arg_parser.output_file_name:
        with open(arg_parser.output_file_name, 'w') as out_file:
            out_file.write(python_source)
        os.chmod(arg_parser.output_file_name,0o755)
    else:
        print("No output file specified, using stdout", file=sys.stderr)
        arg_parser.debug=True
    if arg_parser.debug:
        print(python_source)
        if arg_parser.output_file_name: print('-------------------------------------------')
    return python_source

if __name__=="__main__": run(sys.argv)
