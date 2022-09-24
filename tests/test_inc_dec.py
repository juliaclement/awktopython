#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
""" AWK - Python translator tests
    increment/decrement (++/--) """
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
import re
from helpers import compile_run_answer_assert
from awkpy_runtime import AwkpyRuntimeVarOwner,AwkEmptyVar,AwkEmptyVarInstance

def test_post_inc_arr_uninitialised():
    compile_run_answer_assert(1,"""
BEGIN {
    a[2]=12
    b=a[1]++
    exit b*100+a[1]
}""")

def test_pre_inc_arr_uninitialised():
    compile_run_answer_assert(101,"""
BEGIN {
    a[2]=12
    b=++a[1]
    exit b*100+a[1]
}""")

def test_post_dec_arr_uninitialised():
    compile_run_answer_assert(-1,"""
BEGIN {
    a[2]=12
    b=a[1]--
    exit b*100+a[1]
}""")

def test_pre_dec_arr_uninitialised():
    compile_run_answer_assert(-101,"""
BEGIN {
    a[2]=4
    b=--a[1]
    exit b*100+a[1]
}""")

def test_post_inc_arr_initialised():
    compile_run_answer_assert(809,"""
BEGIN {
    a[1]=8
    b=a[1]++
    exit b*100+a[1]
}""")

def test_pre_inc_arr_initialised():
    compile_run_answer_assert(303,"""
BEGIN {
    a[1]=2
    b=++a[1]
    exit b*100+a[1]
}""")

def test_post_dec_arr_initialised():
    compile_run_answer_assert(908,"""
BEGIN {
    a[1]=9
    b=a[1]--
    exit b*100+a[1]
}""")

def test_pre_dec_arr_initialised():
    compile_run_answer_assert(303,"""
BEGIN {
    a[1]=4
    b=--a[1]
    exit b*100+a[1]
}""")

def test_pre_inc_var_initialised():
    compile_run_answer_assert(202,"""
BEGIN {
    a=1
    b=++a
    exit b*100+a
}""")

def test_post_dec_var_initialised():
    compile_run_answer_assert(302,"""
BEGIN {
    a=3
    b=a--
    exit b*100+a
}""")

def test_post_inc_var_uninitialised():
    compile_run_answer_assert(0,"""
BEGIN {
    b=a++
    exit b+0
}""")

def test_pre_inc_var_uninitialised():
    compile_run_answer_assert(1,"""
BEGIN {
    b=++a
    exit b+0
}""")

def test_post_dec_var_uninitialised():
    compile_run_answer_assert(102,"""
BEGIN {
    a=2
    b=a--
    exit a*100+b
}""")

def test_pre_dec_var_uninitialised():
    compile_run_answer_assert(-2,"""
BEGIN {
    b=--a
    exit a+b
}""")

def test_post_inc_var_initialised():
    compile_run_answer_assert(201,"""
BEGIN {
    a=1
    b=a++
    exit a*100+b
}""")

def test_post_dec_var_initialised2():
    compile_run_answer_assert(708,"""
BEGIN {
    a=8
    b=a--
    exit a*100+b
}""")

def test_pre_dec_var_initialised():
    compile_run_answer_assert(909,"""
BEGIN {
    a=10
    b=--a
    exit a*100+b
}""")

''' The following methods check that if an unknown variable is
    presented, at least the runtime doesn't crash.
    The compiler shouldn't be able to create these conditions
    so we just go straight to the runtime
'''
from awkpy_runtime import AwkpyRuntimeVarOwner

def test_post_dec_var_unknown():
    a=AwkpyRuntimeVarOwner()
    assert a._post_dec_var('balderdash') == 0

def test_pre_dec_var_unknown():
    a=AwkpyRuntimeVarOwner()
    assert a._pre_dec_var('balderdash') == -1

def test_post_inc_var_unknown():
    a=AwkpyRuntimeVarOwner()
    assert a._post_inc_var('balderdash') == 0

def test_pre_inc_var_unknown():
    a=AwkpyRuntimeVarOwner()
    assert a._pre_inc_var('balderdash') == 1
