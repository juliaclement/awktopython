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
from helpers import (
    compile_run_answer_assert,
    compile_run_capsys_assert,
    compile_run,
    Fuzzy,
    full_file_name,
)
from awkpy_compiler import AwkPyCompiler


def test_simple_function_call(capsys):
    compile_run_capsys_assert(
        capsys,
        "fnords.\n",
        """
function fnord() {
    print "fnords."
}
BEGIN {
    fnord()
}""",
    )


def test_function_call_with_args(capsys):
    compile_run_capsys_assert(
        capsys,
        "a is eh\n",
        """
function fnord(a) {
    print "a is "a
}
BEGIN {
    fnord("eh")
}""",
    )


def test_function_setting_globals(capsys):
    compile_run_capsys_assert(
        capsys,
        "replacement\n",
        """
function fnord(a) {
    answer=a
}
BEGIN {
    answer="original"
    fnord("replacement")
    print answer
}""",
    )


def test_function_hiding_globals(capsys):
    compile_run_capsys_assert(
        capsys,
        "original\n",
        """
function fnord(a,answer) {
    answer=a
}
BEGIN {
    answer="original"
    fnord("replacement")
    print answer
}""",
    )


def test_simple_function_call_in_BEGIN():
    compile_run(
        """
function fnord() {
    print "fnords."
}
BEGIN {
    fnord()
}"""
    )


def test_random_function_call():
    compile_run_answer_assert(
        Fuzzy(0.5, 0.5),
        """
BEGIN {
    x=rand()
    y=int(x)
    exit x
}""",
    )


def test_int_function_call():
    compile_run_answer_assert(
        3,
        """
BEGIN {
    y=int(3.2)
    exit y
}""",
    )


def test_atan2_function_call():
    compile_run_answer_assert(
        Fuzzy(1.012197011, 0.0001),
        """
BEGIN {
    y=atan2(8,5)
    exit y
}""",
    )


def test_cos_function_call():
    compile_run_answer_assert(
        Fuzzy(-1, 0.01),
        """
BEGIN {
    y=cos(3.14159265359)
    exit y
}""",
    )


def test_exp_function_call():
    compile_run_answer_assert(
        Fuzzy(7.38905609893065, 0.001),
        """
BEGIN {
    y=exp(2)
    exit y
}""",
    )


def test_gsub_call_basic_nr_changes():
    compile_run_answer_assert(
        2,
        """BEGIN {
    x="Line.1"
    nc=gsub(/[aeiou]/,"(&)",x)
    exit nc
}""",
    )


def test_gsub_call_basic_txt_changes():
    compile_run_answer_assert(
        "L(i)n(e).1",
        """BEGIN {
    x="Line.1"
    nc=gsub(/[aeiou]/,"(&)",x)
    exit x
}""",
    )


def test_gsub_call_string_basic_txt_changes():
    compile_run_answer_assert(
        "L(i)n(e).1",
        """BEGIN {
    x="Line.1"
    nc=gsub("[aeiou]","(&)",x)
    exit x
}""",
    )


def test_gsub_call_variable_regex_txt_changes():
    compile_run_answer_assert(
        "L(i)n(e).1",
        """BEGIN {
    x="Line.1"
    regex="[aeiou]"
    nc=gsub(regex,"(&)",x)
    exit x
}""",
    )


def test_gsub_call_variable_replacement_changes():
    compile_run_answer_assert(
        "L(i)n(e).1",
        """BEGIN {
    x="Line.1"
    repl="(&)"
    nc=gsub(/[aeiou]/,repl,x)
    exit x
}""",
    )


def test_gsub_call_variable_regex_and_replacement_txt_changes():
    compile_run_answer_assert(
        "L(i)n(e).1",
        """BEGIN {
    x="Line.1"
    regex="[aeiou]"
    repl="(&)"
    nc=gsub(regex,repl,x)
    exit x
}""",
    )


def test_gsub_replace_dollar0():
    compile_run_answer_assert(
        "L(i)n(e).1",
        """/Line.1/ {
    nc=gsub(/[aeiou]/,"(&)")
    exit $1
}""",
        [full_file_name("lines.txt")],
    )


def test_gsub_replace_dollar1():
    compile_run_answer_assert(
        "L(i)n(e).2",
        """/Line.2/ {
    nc=gsub(/[aeiou]/,"(&)",$1)
    exit $1
}""",
        [full_file_name("lines.txt")],
    )


def test_log_function_call():
    compile_run_answer_assert(
        Fuzzy(1, 0.001),
        """BEGIN {
    y=log(2.718281828459045)
    exit y
}""",
    )


# compiling for sub & gsub is identical except for
# the maximum number of replacements
# Just testing two simple cases
def test_sub_call_basic_nr_changes():
    compile_run_answer_assert(
        1,
        """BEGIN {
    x="Line.1"
    nc=sub(/[aeiou]/,"(&)",x)
    exit nc
}""",
    )


def test_sub_call_basic_txt_changes():
    compile_run_answer_assert(
        "L(i)ne.1",
        """BEGIN {
    x="Line.1"
    nc=sub(/[aeiou]/,"(&)",x)
    exit x
}""",
    )


def test_sin_function_call():
    compile_run_answer_assert(
        Fuzzy(1, 0.01),
        """
BEGIN {
    y=sin(1.5707963267948966)
    exit y
}""",
    )


def test_sprintf_compiled_d():
    compile_run_answer_assert(
        "7",
        """
BEGIN {
    a=7
    y=sprintf("%d",a)
    exit y
}""",
    )


def test_sprintf_compiled_d_left_aligned():
    compile_run_answer_assert(
        "7  x",
        """
BEGIN {
    a=7
    y=sprintf("%-3dx",a)
    exit y
}""",
    )


def test_sprintf_compiled_d_pre_suffix():
    compile_run_answer_assert(
        ">>7<<",
        """
BEGIN {
    a=7
    y=sprintf(">>%d<<",a)
    exit y
}""",
    )


def test_sprintf_compiled_e():
    compile_run_answer_assert(
        "2.340000e-01",
        """
BEGIN {
    a=0.234
    y=sprintf("%e",a)
    exit y
}""",
    )


def test_sprintf_compiled_f():
    compile_run_answer_assert(
        "2.340000",
        """
BEGIN {
    a=2.34
    y=sprintf("%8.6f",a)
    exit y
}""",
    )


def test_sprintf_compiled_g_to_f():
    compile_run_answer_assert(
        "2112728.4",
        r"""BEGIN{ exit sprintf("%g", 2112728.4);}""",
    )


def test_sprintf_compiled_g_to_e():
    compile_run_answer_assert(
        "2.112728e+14",
        r"""BEGIN{ exit sprintf("%g", 211272800000000.4);}""",
    )


def test_sprintf_compiled_G_to_E():
    compile_run_answer_assert(
        "2.112728E+14",
        r"""BEGIN{ exit sprintf("%G", 211272800000000.4);}""",
    )


def test_sprintf_compiled_f_4dp():
    compile_run_answer_assert(
        "2.3400",
        """
BEGIN {
    a=2.34
    y=sprintf("%.4f",a)
    exit y
}""",
    )


def test_sprintf_compiled_f_width_in_args():
    compile_run_answer_assert(
        " 12.3450",
        """
BEGIN {
    a=12.345
    y=sprintf("%*.*f",8,4,a)
    exit y
}""",
    )


def test_sprintf_compiled_g_to_f():
    compile_run_answer_assert(
        "2112728.4",
        r"""BEGIN{ fmt="%g"; exit sprintf(fmt, 2112728.4);}""",
    )


def test_sprintf_compiled_g_to_e():
    compile_run_answer_assert(
        "2.112728e+14",
        r"""BEGIN{ fmt="%g"; exit sprintf(fmt, 211272800000000.4);}""",
    )


def test_sprintf_compiled_G_to_E():
    compile_run_answer_assert(
        "2.112728E+14",
        r"""BEGIN{ fmt="%G"; exit sprintf(fmt, 211272800000000.4);}""",
    )


def test_sprintf_compiled_i():  # POSIX spec says synonym for d
    compile_run_answer_assert(
        "7",
        """
BEGIN {
    a=7
    y=sprintf("%i",a)
    exit y
}""",
    )


def test_sprintf_compiled_o():
    compile_run_answer_assert(
        "23",
        """
BEGIN {
    a=19
    y=sprintf("%o",a)
    exit y
}""",
    )


def test_sprintf_compiled_s():
    compile_run_answer_assert(
        "7-Up",
        """
BEGIN {
    a="7-Up"
    y=sprintf("%s",a)
    exit y
}""",
    )


def test_sprintf_compiled_s_repls():
    compile_run_answer_assert(
        "%{7-Up}%",
        """
BEGIN {
    a="7-Up"
    y=sprintf("%%{%s}\\%",a)
    exit y
}""",
    )


def test_sprintf_compiled_s_using_count():
    compile_run_answer_assert(
        "Two One",
        """
BEGIN {
    a="One"
    b="Two"
    y=sprintf("%2$s %1$s",a,b)
    exit y
}""",
    )


def test_sprintf_compiled_x():
    compile_run_answer_assert(
        "13",
        """
BEGIN {
    a=19
    y=sprintf("%x",a)
    exit y
}""",
    )


def test_sprintf_compiled_dollar():
    compile_run_answer_assert(
        "1 1.230000 1.23",
        r"""BEGIN {a=1.23;exit sprintf("%1$d %1$f %1$s",a);}""",
    )


def test_sprintf_interpreted_d():
    compile_run_answer_assert(
        "7",
        """
BEGIN {
    a=7
    fmt="%d"
    y=sprintf(fmt,a)
    exit y
}""",
    )


def test_sprintf_interpreted_d_left_aligned():
    compile_run_answer_assert(
        "7  x",
        """
BEGIN {
    a=7
    fmt="%-3dx"
    y=sprintf(fmt,a)
    exit y
}""",
    )


def test_sprintf_interpreted_d_pre_suffix():
    compile_run_answer_assert(
        ">>7<<",
        """
BEGIN {
    a=7
    fmt=">>%d<<"
    y=sprintf(fmt,a)
    exit y
}""",
    )


def test_sprintf_interpreted_f():
    compile_run_answer_assert(
        "12.345000",
        """
BEGIN {
    a=12.345
    fmt="%f"
    y=sprintf(fmt,a)
    exit y
}""",
    )


def test_sprintf_interpreted_f_width_in_args():
    compile_run_answer_assert(
        " 12.3450",
        """
BEGIN {
    a=12.345
    fmt="%*.*f"
    y=sprintf(fmt,8,4,a)
    exit y
}""",
    )


def test_sprintf_interpreted_f_4dp():
    compile_run_answer_assert(
        "12.3450",
        """
BEGIN {
    a=12.345
    fmt="%.4f"
    y=sprintf(fmt,a)
    exit y
}""",
    )


def test_sprintf_interpreted_i():  # POSIX spec says synonym for d
    compile_run_answer_assert(
        "7",
        """
BEGIN {
    a=7
    fmt="%i"
    y=sprintf(fmt,a)
    exit y
}""",
    )


def test_sprintf_interpreted_o():
    compile_run_answer_assert(
        "23",
        """
BEGIN {
    a=19
    fmt="%o"
    y=sprintf(fmt,a)
    exit y
}""",
    )


def test_sprintf_interpreted_s():
    compile_run_answer_assert(
        "7-Up",
        """
BEGIN {
    a="7-Up"
    fmt="%s"
    y=sprintf(fmt,a)
    exit y
}""",
    )


def test_sprintf_interpreted_s_repls():
    compile_run_answer_assert(
        "%{7-Up}%",
        """
BEGIN {
    a="7-Up"
    fmt="%%{%s}%%"
    y=sprintf(fmt,a)
    exit y
}""",
    )


def test_sprintf_interpreted_s_using_count():
    compile_run_answer_assert(
        "Two One",
        """
BEGIN {
    a="One"
    b="Two"
    fmt="%2$s %1$s"
    y=sprintf(fmt,a,b)
    exit y
}""",
    )


def test_sprintf_interpreted_x():
    compile_run_answer_assert(
        "13",
        """
BEGIN {
    a=19
    fmt="%x"
    y=sprintf(fmt,a)
    exit y
}""",
    )


def test_sprintf_interpreted_dollar():
    compile_run_answer_assert(
        "1 1.230000 1.23",
        r"""BEGIN {fmt="%1$d %1$f %1$s";a=1.23;exit sprintf(fmt,a);}""",
    )


def test_sqrt_function_call():
    compile_run_answer_assert(
        Fuzzy(4, 0.00001),
        """
BEGIN {
    y=sqrt(16)
    exit y
}""",
    )


def test_split_function_call_2_args_1():
    compile_run_answer_assert(
        "123",
        """
BEGIN {
    x="123./456..789.101112"
    FS="./"
    split(x,y)
    exit y[1]
}""",
    )


def test_split_function_call_2_args_2():
    compile_run_answer_assert(
        "456..789.101112",
        """
BEGIN {
    x="123./456..789.101112"
    FS="./"
    split(x,y)
    exit y[2]
}""",
    )


def test_split_function_call_3_args_1():
    compile_run_answer_assert(
        "123",
        """
BEGIN {
    x="123./456..789.101112"
    split(x,y,"./")
    exit y[1]
}""",
    )


def test_split_function_call_3_args_2():
    compile_run_answer_assert(
        "456..789.101112",
        """
BEGIN {
    x="123./456..789.101112"
    split(x,y,"./")
    exit y[2]
}""",
    )


def test_substr_function_call_1():
    compile_run_answer_assert(
        "3456",
        """
BEGIN {y="123456"
    z=substr(y,3)
    exit z
}""",
    )


def test_substr_function_call_1_underflow_1():
    compile_run_answer_assert(
        "123456",
        """
BEGIN {y="123456"
    z=substr(y,-3)
    exit z
}""",
    )


def test_substr_function_call_1_underflow_2():
    compile_run_answer_assert(
        "123456",
        """
BEGIN {y="123456"
    w=-3
    z=substr(y,w)
    exit z
}""",
    )


def test_substr_function_call_2_overflow_1():
    compile_run_answer_assert(
        "",
        """
BEGIN {y="123456"
    z=substr(y,8,6)
    exit z
}""",
    )


def test_substr_function_call_2_overflow_2():
    compile_run_answer_assert(
        "",
        """
BEGIN {y="123456"
    start=8
    size=6
    z=substr(y,start,size)
    exit z
}""",
    )


def test_substr_function_call_2():
    compile_run_answer_assert(
        "34",
        """
BEGIN {y="123456"
    z=substr(y,3,2)
    exit z
}""",
    )


def test_substr_function_call_1_expr():
    compile_run_answer_assert(
        "3456",
        """
BEGIN {a="123456"
    b=2+1
    c=substr(a,b)
    exit c
}""",
    )


def test_substr_function_call_2_expr():
    compile_run_answer_assert(
        "34",
        """
BEGIN {a="123456"
    b=2+1
    c=b-1
    d=substr(a,b,c)
    exit d
}""",
    )


def test_toupper_function_call():
    compile_run_answer_assert(
        "BANG",
        """
BEGIN {a="Bang"
    b=toupper(a)
    exit b
}""",
    )


def test_tolower_function_call():
    compile_run_answer_assert(
        "whimper",
        """
BEGIN {a="Whimper"
    b=tolower(a)
    exit b
}""",
    )
