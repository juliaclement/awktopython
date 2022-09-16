#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
""" AWK - Python translator tests
    block (BEGIN/END/mainloop) functionality """ 
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
from helpers import compile_run_answer_assert,compile_run_capsys_assert,full_file_name,compile_run

def test_maths(capsys):
    compile_run_capsys_assert(capsys,'3\n','''
BEGIN {
    Abc=1;
    Abc=Abc+2;
    print Abc
}''')

def test_for_python_style():
    compile_run_answer_assert( 75,'''
BEGIN {
    for(i=10; i<16; ++i) {
        t[i]=i
    }
    total=0
    for (s in t) {
        total+=s
    }
    exit total
}''')

def test_for(capsys):
    compile_run_capsys_assert( capsys,'1:5\n','''
BEGIN {
    i=0;
    t=6;
    for(i=0; t>1; --t) {
        i+=1;
    }
    print t":"i
}''')

def test_for_no_init():
    compile_run_answer_assert( 105,'''
BEGIN {
    i=0;
    t=6;
    for(; t>1; --t) {
        i+=1;
    }
    exit t*100+i
}''')

def test_for_no_test():
    compile_run_answer_assert( 105,'''
BEGIN {
    i=0;
    t=6;
    for(i=0;; --t) {
        if (t < 2) {
            break;
        }
        i+=1;
    }
    exit t*100+i
}''')

def test_for_no_increment():
    compile_run_answer_assert( 105,'''
BEGIN {
    i=0;
    t=6;
    for(i=0; t>1;) {
        i+=1;
        t-=1;
    }
    exit t*100+i
}''')

def test_while(capsys):
    compile_run_capsys_assert( capsys,'1:5\n','''
BEGIN {
    i=0;
    t=6;
    while(t>1) {
        t-=1;
        i+=1;
    }
    print t":"i
}''')

def test_continue(capsys):
    compile_run_capsys_assert(capsys,'1:1\n','''
BEGIN {
    i=1;
    t=6;
    while(t>1) {
        t-=1;
        continue
        i+=1;
    }
    print t":"i
}''')

def test_break(capsys):
    compile_run_capsys_assert(capsys,'5:1\n','''
BEGIN {
    i=1;
    t=6;
    while(t>1) {
        t-=1;
        break
        i+=1;
    }
    print t":"i
}''')

def test_do(capsys):
    awk='''
BEGIN {
    i=0;
    t=6;
    do {
        t-=1;
        i+=1;
    } while(t>0);
    print t":"i
}'''
    compile_run(awk)
    captured = capsys.readouterr()
    assert captured.out == '0:6\n'

def test_if_else(capsys):
    awk='''
BEGIN {
    i=0;
    t=6;
    if( i > t ) {
        print "Wrong"
    } else
        print "OK";
}'''
    compile_run(awk)
    captured = capsys.readouterr()
    assert captured.out == 'OK\n'

def test_function_condition_block():
    compile_run_answer_assert(1,'''
function f(a) {
    if(a=="Line.3") {
        return 1;
    }
    return 0;
}
f($1) > 0 {exit f($1)}''',[full_file_name('lines.txt')])

# txst_function_condition_block()
