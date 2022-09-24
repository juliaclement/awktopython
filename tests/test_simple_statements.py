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

import pytest
from os import environ
from helpers import compile_run_answer_assert, compile_run_capsys_assert, full_file_name, check_arg_parser

def test_simple_match(capsys):
    compile_run_capsys_assert(capsys,"Duplicated\n",'/a/ { print $3 }',[full_file_name('lines.txt')])

def test_word_test(capsys):
    compile_run_capsys_assert(capsys,"Line.3\n",'$1=="Line.3" {print $1}',[full_file_name('lines.txt')])

# should quietly interpret  print as print $0 
def test_print_empty(capsys):
    compile_run_capsys_assert(capsys,"Line.1\n",'$1=="Line.1" {print}',[full_file_name('lines.txt')])

def test_print_number(capsys):
    compile_run_capsys_assert(capsys,"3\n",'$1=="Line.1" {print 3}',[full_file_name('lines.txt')])

# check(parser,compiler_options,runtime_options,variables)
def test_arg_debug():
    check_arg_parser(True, lambda p,c,r,v: p.debug, ["-ofilename","{a=b;}","-d"])

def test_arg_code():
    check_arg_parser("-e{a=b;}", lambda p,c,r,v: c[0], ["{a=b;}","-d"])

def test_arg_e_code1():
    check_arg_parser("-e{a=b;}", lambda p,c,r,v: c[0], ["-e{a=b;}","-d"])

def test_arg_e_code2():
    check_arg_parser("-e{a=b;}", lambda p,c,r,v: c[0], ["-e","{a=b;}","-d"])
    
def test_arg_datafilename1():
    check_arg_parser("sourcefilename", lambda p,c,r,v: r[0], ["{a=b;}","sourcefilename"])

def test_arg_datafilename2():
    check_arg_parser("sourcefilename", lambda p,c,r,v: r[0], ["{a=b;}","--","sourcefilename"])
test_arg_datafilename2()
    
def test_arg_sourcefilename1():
    check_arg_parser("-fsourcefilename", lambda p,c,r,v: c[0], ["-fsourcefilename","{a=b;}"])

def test_arg_sourcefilename2():
    check_arg_parser("-fsourcefilename", lambda p,c,r,v: c[0], ["-f","sourcefilename","{a=b;}"])
    
def test_arg_output_file_name1():
    check_arg_parser("filename", lambda p,c,r,v: p.output_file_name, ["-ofilename","{a=b;}"])

def test_arg_foutput_file_name2():
    check_arg_parser("filename", lambda p,c,r,v: p.output_file_name, ["-o","filename","{a=b;}"])

def test_arg_variable1():
    check_arg_parser("-va=b", lambda p,c,r,v: v[0], ["-va=b", "{print a;}"])

def test_arg_variable2():
    check_arg_parser("-va=b", lambda p,c,r,v: v[0], ["-v", "a=b", "{print a;}"])

def test_negative_number():
    compile_run_answer_assert(-3,'''
BEGIN {
    a = -1
    b = a - 2
    exit b
}''',[full_file_name('lines.txt')])

def test_exit():
    compile_run_answer_assert(0,'''
BEGIN {
    print "X"
    exit
}
{print $1
exit 1}''',[full_file_name('lines.txt')])

def test_exit_num():
    compile_run_answer_assert(2,'''
BEGIN {
    print "X"
    exit 2
}
{print $1}''',[full_file_name('lines.txt')])

def test_OFS(capsys):
    compile_run_capsys_assert(capsys,'left-right\n','''
END {
    OFS="-"
    l="left";
    r="right";
    print l,r
}''')

def test_nextfile(capsys):
    compile_run_capsys_assert(capsys,"Duplicated\n",'/D/ { print $3; nextfile }',[full_file_name('lines.txt')])

def test_regex():
    compile_run_answer_assert(1,'''
BEGIN {
    var="start"
    if( var~/a/ ) exit 1
    exit 0
}
    ''')

def test_not_regex():
    compile_run_answer_assert(1,'''
BEGIN {
    var="begin"
    if( var!~/a/ ) exit 1
    exit 0
}
    ''')

def test_regex_in_string():
    compile_run_answer_assert(1,'''
BEGIN {
    var="start"
    astr=substr("string",3,1)
    if( var~astr ) exit 1
    exit 0
}
    ''')

def test_regex_as_block():
    compile_run_answer_assert(1,'''BEGIN {
    var="start"
    astr=substr("Duplicated",3,1)
    exit_code=0
}
$3~astr {exit_code=1; exit 1;}
END {
    exit exit_code
}''',[full_file_name('lines.txt')])

def test_array_print(capsys):
    compile_run_capsys_assert(capsys,'value\n','''
BEGIN {
    a[1]="value"
}
END {
    print a[1]
}
    ''')

def test_array(capsys):
    compile_run_capsys_assert(capsys,'value\n','''
BEGIN {
    a[1]="alue"
}
END {
    q =  "v" a[1]
    print q
}
    ''')

def test_string_concat_2_vars():
    compile_run_answer_assert("lllrrr",'''
BEGIN {
    l="lll"
    r="rrr"
    x=l r
    exit x
}
    ''')

def test_string_concat_var_str():
    compile_run_answer_assert("lllrrr",'''
BEGIN {
    l="lll"
    x=l "rrr"
    exit x
}
    ''')

def test_string_concat_str_var():
    compile_run_answer_assert("lllrrr",'''
BEGIN {
    r="rrr"
    x="lll" r
    exit x
}
    ''')

def test_string_concat_2_str():
    compile_run_answer_assert("lllrrr",'''
BEGIN {
    x="lll" "rrr"
    exit x
}
    ''')

def test_print_concat(capsys):
    compile_run_capsys_assert(capsys,'<><>\n','''    
BEGIN {
    a="<>"
    print a a
}
    ''')

def test_array_concat_2_strs():
    compile_run_answer_assert("<><>",'''
BEGIN {
    a[1]="<>"
    b = a[1] a[1]
    exit b
}
    ''')

def test_print_concat_array_2(capsys):
    compile_run_capsys_assert(capsys,'<><>\n','''
BEGIN {
    a[1]="<>"
    print a[1] a[1]
}
    ''')

def test_ENVIRON_found():
    assert environ['PATH'] != ''
    compile_run_answer_assert(environ['PATH'],'''
BEGIN {
    exit ENVIRON["PATH"]
}
    ''')

def test_ENVIRON_not_found():
    compile_run_answer_assert('xx','''
BEGIN {
    a="x" ENVIRON["AwkEmptyVar"] "x"
    exit a
}
    ''')

def test_print_ENVIRON_found(capsys):
    assert environ['PATH'] != ''
    compile_run_capsys_assert(capsys,environ['PATH']+'\n','''
BEGIN {
    print ENVIRON["PATH"]
}
    ''')

def test_print_ENVIRON_not_found(capsys):
    compile_run_capsys_assert(capsys,'xx\n','''
BEGIN {
    print "x" ENVIRON["AwkEmptyVar"] "x"
}
    ''')

