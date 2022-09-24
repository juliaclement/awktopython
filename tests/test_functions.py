#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
""" AWK - Python translator tests
    test functions """ 
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
import math
from helpers import compile_run_answer_assert, compile_run_capsys_assert, compile_run, Fuzzy
from awkpy_compiler import AwkPyCompiler

def test_simple_function_call(capsys):
    compile_run_capsys_assert(capsys,"fnords.\n",'''
function fnord() {
    print "fnords."
}
BEGIN {
    fnord()
}''')

def test_function_call_with_args(capsys):
    compile_run_capsys_assert(capsys,"a is eh\n",'''
function fnord(a) {
    print "a is "a
}
BEGIN {
    fnord("eh")
}''')

def test_function_setting_globals(capsys):
    compile_run_capsys_assert(capsys,"replacement\n",'''
function fnord(a) {
    answer=a
}
BEGIN {
    answer="original"
    fnord("replacement")
    print answer
}''')

def test_function_hiding_globals(capsys):
    compile_run_capsys_assert(capsys,"original\n",'''
function fnord(a,answer) {
    answer=a
}
BEGIN {
    answer="original"
    fnord("replacement")
    print answer
}''')

def test_simple_function_call_in_BEGIN():
    compile_run('''
function fnord() {
    print "fnords."
}
BEGIN {
    fnord()
}''')

def test_random_function_call():
    compile_run_answer_assert(Fuzzy(0.5,0.5),'''
BEGIN {
    x=rand()
    y=int(x)
    exit x
}''')

def test_int_function_call():
    compile_run_answer_assert(3,'''
BEGIN {
    y=int(3.2)
    exit y
}''')

def test_atan2_function_call():
    compile_run_answer_assert(Fuzzy(1.012197011,0.0001),'''
BEGIN {
    y=atan2(8,5)
    exit y
}''')

def test_cos_function_call():
    compile_run_answer_assert(Fuzzy(-1,0.01),'''
BEGIN {
    y=cos(3.14159265359)
    exit y
}''')

def test_exp_function_call():
    compile_run_answer_assert(Fuzzy(7.38905609893065,0.001),'''
BEGIN {
    y=exp(2)
    exit y
}''')

def test_sin_function_call():
    compile_run_answer_assert(Fuzzy(1,0.01),'''
BEGIN {
    y=sin(1.5707963267948966)
    exit y
}''')

def test_sqrt_function_call():
    compile_run_answer_assert(Fuzzy(4,0.00001),'''
BEGIN {
    y=sqrt(16)
    exit y
}''')

def test_split_function_call_2_args_1():
    compile_run_answer_assert('123','''
BEGIN {
    x="123./456..789.101112"
    FS="./"
    split(x,y)
    exit y[1]
}''')

def test_split_function_call_2_args_2():
    compile_run_answer_assert('456..789.101112','''
BEGIN {
    x="123./456..789.101112"
    FS="./"
    split(x,y)
    exit y[2]
}''')

def test_split_function_call_3_args_1():
    compile_run_answer_assert('123','''
BEGIN {
    x="123./456..789.101112"
    split(x,y,"./")
    exit y[1]
}''')

def test_split_function_call_3_args_2():
    compile_run_answer_assert('456..789.101112','''
BEGIN {
    x="123./456..789.101112"
    split(x,y,"./")
    exit y[2]
}''')

def test_substr_function_call_1():
    compile_run_answer_assert('3456','''
BEGIN {y="123456"
    z=substr(y,3)
    exit z
}''')

def test_substr_function_call_1_underflow_1():
    compile_run_answer_assert('123456','''
BEGIN {y="123456"
    z=substr(y,-3)
    exit z
}''')

def test_substr_function_call_1_underflow_2():
    compile_run_answer_assert('123456','''
BEGIN {y="123456"
    w=-3
    z=substr(y,w)
    exit z
}''')

def test_substr_function_call_2_overflow_1():
    compile_run_answer_assert('','''
BEGIN {y="123456"
    z=substr(y,8,6)
    exit z
}''')

def test_substr_function_call_2_overflow_2():
    compile_run_answer_assert('','''
BEGIN {y="123456"
    start=8
    size=6
    z=substr(y,start,size)
    exit z
}''')

def test_substr_function_call_2():
    compile_run_answer_assert('34','''
BEGIN {y="123456"
    z=substr(y,3,2)
    exit z
}''')

def test_substr_function_call_1_expr():
    compile_run_answer_assert('3456','''
BEGIN {a="123456"
    b=2+1
    c=substr(a,b)
    exit c
}''')

def test_substr_function_call_2_expr():
    compile_run_answer_assert('34','''
BEGIN {a="123456"
    b=2+1
    c=b-1
    d=substr(a,b,c)
    exit d
}''')

def test_toupper_function_call():
    compile_run_answer_assert('BANG','''
BEGIN {a="Bang"
    b=toupper(a)
    exit b
}''')

def test_tolower_function_call():
    compile_run_answer_assert('whimper','''
BEGIN {a="Whimper"
    b=tolower(a)
    exit b
}''')
