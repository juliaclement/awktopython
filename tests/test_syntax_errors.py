#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
""" AWK - Python translator tests
    test that the compiler behaves directly when AWK code has
    syntax errors.
    
    NB: The translator is designed to translate already known
        to be valid & correct AWK, so the syntax checking is 
        minimal by design
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

import pytest
from pathlib import Path
from awkpy_compiler import AwkPyCompiler


def compile_catch(awk: str, expected=None):
    compiler = AwkPyCompiler(debug=False)
    error_found = False
    error_msg = "No exception raised"
    try:
        compiler.compile(awk)
    except SyntaxError as err:
        print(err.msg)
        error_found = True
        error_msg = err.msg
    assert error_found, error_msg
    return error_msg


def test_braces_closed():
    compile_catch("""$1=="" { xxxxx""")


def test_parentheses_closed():
    compile_catch("""$1=="" { (xxxxx;}""")


def test_brackets_closed():
    compile_catch("""$1=="" { xxxxx[1 = 12}""")


def test_operators_apart():
    compile_catch("""$1=="" { xxxxx=xxxxxx * / 3}""")


def test_sections_are_blocks():
    compile_catch("""BEGIN xxxxx=xxxxxx *3}""")


def test_conditions_start_well():
    compile_catch("""] {xxxxx=xxxxx *3}""")


def test_statements_at_file_level_are_blocks():
    compile_catch("""xxxxx=xxxxxx*3;""")


def test_statements_at_file_level_are_blocks_2():
    compile_catch("""(xxxxx=xxxxxx*3);""")


def test_regex_starts_with_slash():
    compile_catch("""{if ($1~"string") print $0}""")
