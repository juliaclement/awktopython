#!/usr/bin/python3
"""
    AWK to python translator: compile and go.
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
import re
import subprocess
import os
import random
import math
from pathlib import Path
from collections import defaultdict
from awkpy_compiler import AwkPyCompiler
from awkpy_runtime import (
    AwkpyRuntimeVarOwner,
    AwkpyRuntimeWrapper,
    AwkNext,
    AwkNextFile,
    AwkExit,
    AwkEmptyVar,
    AwkEmptyVarInstance,
)
from awkpy_common import AwkPyArgParser


def run(args):
    compiler = AwkPyCompiler(debug=False)
    compiler_args = []
    runtime_args = []
    arg_parser = AwkPyArgParser(compiler_args, runtime_args, compiler_args)
    arg_parser.parse(args)
    compiler.do_debug = arg_parser.debug
    python_source = compiler.compile(compiler_args) + "\nruntime=AwkPyTranslated()\n"
    if arg_parser.output_file_name:
        with open(arg_parser.output_file_name, "w") as out_file:
            out_file.write(python_source)
            out_file.write(f"runtime._run(sys.argv[1:])\n")
        os.chmod(arg_parser.output_file_name, 0o755)
    #
    # non-standard command-line option -Wr = All following args
    # bypass the compiler & are passed to the execution runtime.
    # (Name = W=Posix recomendation for extensions, r=runtime)
    if len(runtime_args) > 0 and runtime_args[0] == "-Wr":
        wr = runtime_args
        wr[0] = arg_parser.program_name
        runtime_args = []
        arg_parser = AwkPyArgParser(runtime_args, runtime_args, runtime_args)
        arg_parser.parse(wr)
    runtime_args.insert(0, arg_parser.program_name)
    python_source += f"runtime._run({runtime_args})\n"
    if arg_parser.debug:
        print(python_source)
        print("-------------------------------------------")
    code = compile(python_source, "generated", "exec")
    exec(code, globals(), locals())
    return AwkpyRuntimeWrapper._ans


if __name__ == "__main__":
    run(sys.argv)
    # file='/home/julia/Projects/python/awktopython/tests/lines.txt'
    # run(['awkpy_out','-v', 'A=File.1', '$1=="Line.4"{print A","$1}',file, 'A=File.2', file])
    exit(AwkpyRuntimeWrapper._ans)
