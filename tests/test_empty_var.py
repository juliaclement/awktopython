#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
""" AWK - Python translator tests
    exercise AwkEmptyVar dunders """ 
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
from awkpy_runtime import AwkEmptyVar

def test_empty_var_str():
    assert AwkEmptyVar() == ""

def test_empty_var_str_cast():
    assert str(AwkEmptyVar()) == ""

def test_empty_var_int():
    assert AwkEmptyVar() == 0

def test_empty_var_int_cast():
    assert int(AwkEmptyVar()) == 0

def test_empty_var_float():
    assert AwkEmptyVar() == 0.0

def test_empty_var_float_cast():
    assert float(AwkEmptyVar()) == 0.0

def test_empty_var_bool():
    assert not AwkEmptyVar()

def test_empty_var_bool_cast():
    assert bool(AwkEmptyVar()) == False

def test_empty_var_add():
    a=AwkEmptyVar()
    b=a+2
    assert b==2

def test_empty_var_abs():
    a=AwkEmptyVar()
    b=abs(a)+2
    assert b==2

def test_empty_var_neg():
    a=AwkEmptyVar()
    b=-a+2
    assert b==2

def test_empty_var_pos():
    a=AwkEmptyVar()
    b=+a
    assert b==0

def test_empty_var_invert():
    a=AwkEmptyVar()
    b=~a
    c=~0
    assert b==c

def test_empty_var_sub():
    a=AwkEmptyVar()
    b=a-2
    assert b==-2

def test_empty_var_mult():
    a=AwkEmptyVar()
    b=a*2
    assert b==0

def test_empty_var_div():
    a=AwkEmptyVar()
    b=a/2
    assert b==0

def test_empty_var_truediv():
    a=AwkEmptyVar()
    b=a/2.0
    assert b==0

def test_empty_var_mod():
    a=AwkEmptyVar()
    b=a%2
    assert b==0

def test_empty_var_floordiv():
    a=AwkEmptyVar()
    b=a//2.0
    assert b==0

def test_empty_var_pow():
    a=AwkEmptyVar()
    b=a**2
    assert b==0

def test_empty_var_rtruediv():
    a=AwkEmptyVar()
    b=a//2
    assert b==0

def test_empty_var_iadd():
    a=AwkEmptyVar()
    a+=2
    assert a==2

def test_empty_var_isub():
    a=AwkEmptyVar()
    a-=2
    assert a==-2

def test_empty_var_imul():
    a=AwkEmptyVar()
    a*=2
    assert a==0

def test_empty_var_imod():
    a=AwkEmptyVar()
    a%=2
    assert a==0

def test_empty_var_idiv():
    a=AwkEmptyVar()
    a/=2
    assert a==0

def test_empty_var_ifloordiv():
    a=AwkEmptyVar()
    a//=2
    assert a==0

def test_empty_var_ipow():
    a=AwkEmptyVar()
    a**=2
    assert a==0

def test_empty_var_ilsh():
    a=AwkEmptyVar()
    a<<=2
    assert a==0

def test_empty_var_irsh():
    a=AwkEmptyVar()
    a>>=2
    assert a==0

def test_empty_var_iand():
    a=AwkEmptyVar()
    a&=~0
    assert a==0

def test_empty_var_ior():
    a=AwkEmptyVar()
    a|=2
    assert a==2

def test_empty_var_ixor():
    a=AwkEmptyVar()
    a^=2
    assert a==2

def test_empty_var_radd():
    a=AwkEmptyVar()
    b=2+a
    assert b==2

def test_empty_var_rsub():
    a=AwkEmptyVar()
    b=2-a
    assert b==2

def test_empty_var_rmult():
    a=AwkEmptyVar()
    b=2*a
    assert b==0

def test_empty_var_rpow():
    a=AwkEmptyVar()
    b=2**a
    assert b==1

def test_empty_var_rdiv():
    a=AwkEmptyVar()
    got_exception = False
    try:
        b=2/a
    except ZeroDivisionError:
        got_exception = True
    assert got_exception

def test_empty_var_rfloordiv():
    a=AwkEmptyVar()
    got_exception = False
    try:
        b=2//a
    except ZeroDivisionError:
        got_exception = True
    assert got_exception

def test_empty_var_rmod():
    a=AwkEmptyVar()
    got_exception = False
    try:
        b=2%a
    except ZeroDivisionError:
        got_exception = True
    assert got_exception

def test_empty_var_rand():
    a=AwkEmptyVar()
    b=2&a
    assert b==0

def test_empty_var_ror():
    a=AwkEmptyVar()
    b=2|a
    assert b==2

def test_empty_var_rxor():
    a=AwkEmptyVar()
    b=2^a
    assert b==2

def test_empty_var_rlshift():
    a=AwkEmptyVar()
    b=2<<a
    assert b==2

def test_empty_var_rrshift():
    a=AwkEmptyVar()
    b=2>>a
    assert b==2

def test_empty_var_concat():
    a=AwkEmptyVar()
    b=a+"x"
    assert b=="x"

def test_empty_var_repr():
    assert AwkEmptyVar().__repr__() == 'AwkEmptyVar()'
