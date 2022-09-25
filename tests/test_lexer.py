#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
""" AWK - Python translator tests
    of the lexer, including the tokenizer and namespaces """
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

import io
import pytest
from pathlib import Path
import math
import sys
from helpers import full_file_name, Fuzzy, compile_run_answer_assert

try:
    from awkpy_compiler import AwkPyCompiler, AwkNamespace
except:
    path = Path(__file__).parent.parent / "code"
    sys.path.append(str(path))
    from awkpy_compiler import AwkPyCompiler, AwkNamespace
""" Test AwkNamespace class"""


def test_ns_decorations():
    ns = AwkNamespace("smurf")
    assert ns.name == "smurf"
    assert ns.decorated == "smurf::"
    assert ns.python_equivalent == "self.smurf__"


def test_ns_decorations_for_predefined_awk():
    ns = AwkNamespace.awk_awk_namespace
    assert ns.name == "awk"
    assert ns.decorated == ""
    assert ns.python_equivalent == "self."


def test_ns_decorations_unchanged_for_awk():
    ns = AwkNamespace("awk")
    assert ns.name == "awk"
    assert ns.decorated == ""
    assert ns.python_equivalent == "self."


def test_ns_UCASE_is_awk():
    AwkNamespace.set_current_namespace("smurf")
    ns = AwkNamespace.find_ns("RS")
    assert ns.name == "awk"


def test_ns_non_ucase_is_current():
    AwkNamespace.set_current_namespace("smurf")
    ns = AwkNamespace.find_ns("BrainySmurf")
    assert ns.name == "smurf"


def test_ns_decorated_name():
    ns = AwkNamespace.find_ns("smurf::smurfette")
    assert ns.name == "smurf"


def test_ns_no_duplicates_1():
    ns1 = AwkNamespace.get_namespace("Peyo")
    assert ns1.name == "Peyo"
    ns2 = AwkNamespace.get_namespace("Peyo")
    assert ns2.name == "Peyo"
    assert ns1 is ns2


def test_ns_no_duplicates_2():
    ns1 = AwkNamespace.find_ns("smurf::smurfette")
    assert ns1.name == "smurf"
    ns2 = AwkNamespace.find_ns("smurf::papasmurf")
    assert ns2.name == "smurf"
    assert ns1 is ns2


def test_ns_no_duplicates_3():
    ns1 = AwkNamespace("De_Smurfen")
    assert ns1.name == "De_Smurfen"
    ns2 = AwkNamespace("De_Smurfen")
    assert ns2.name == "De_Smurfen"
    assert ns1 is ns2


def test_set_current_namespace():
    oldns1 = AwkNamespace.awk_current_namespace
    oldns2 = AwkNamespace.set_current_namespace("smurf")
    assert oldns1 is oldns2
    assert AwkNamespace.awk_current_namespace.name == "smurf"
    oldns3 = AwkNamespace.set_current_namespace("schtroumpfs")
    assert oldns3.name == "smurf"
    assert AwkNamespace.awk_current_namespace.name == "schtroumpfs"
    AwkNamespace.set_current_namespace(oldns2)
    assert AwkNamespace.get_current_namespace() is oldns2


def test_namespace_ignores_UCASE_vars():
    compile_run_answer_assert(
        "smurfette",
        """BEGIN {
    VAR="start"
    @namespace "smurf"
    VAR="smurfette"
    @namespace "awk"
    exit VAR
}""",
    )


def test_namespace_seperates_vars_1():
    compile_run_answer_assert(
        "start",
        """BEGIN {
    var="start"
    @namespace "smurf"
    var="smurfette"
    @namespace "awk"
    exit var
}""",
    )


def test_namespace_seperates_vars_2():
    compile_run_answer_assert(
        "smurfette",
        """BEGIN {
    var="start"
    @namespace "smurf"
    var="smurfette"
    @namespace "awk"
    exit smurf::var
}""",
    )


def test_namespace_qualified_vars_1():
    compile_run_answer_assert(
        "papasmurf",
        """BEGIN {
    var="start"
    @namespace "smurf"
    var="smurfette"
    @namespace "awk"
    smurf::var="papasmurf"
    awk::var="varnish"
    @namespace "smurf"
    exit var
}""",
    )


def test_namespace_resident_functions_1():
    compile_run_answer_assert(
        "shhhh",
        """
    function squirrel() {
        return "squeak"
    }
    @namespace "secret"
    function squirrel() {
        return "shhhh"
    }
    BEGIN {
        exit squirrel()
}""",
    )


def test_namespace_resident_functions_2():
    compile_run_answer_assert(
        "squeak",
        """
    function squirrel() {
        return "squeak"
    }
    @namespace "secret"
    function squirrel() {
        return "shhhh"
    }
    BEGIN {
        @namespace "awk"
        exit squirrel()
}""",
    )


def test_cross_namespace_function_calls_1():
    compile_run_answer_assert(
        "squeak",
        """
    function squirrel() {
        return "squeak"
    }
    @namespace "normal"
    function squirrel() {
        return "tsk"
    }
    @namespace "secret"
    function squirrel() {
        return "shhhh"
    }
    @namespace "awk"
    BEGIN {
        exit squirrel()
}""",
    )


def test_cross_namespace_function_calls_2():
    compile_run_answer_assert(
        "tsk",
        """
    function squirrel() {
        return "squeak"
    }
    @namespace "normal"
    function squirrel() {
        return "tsk"
    }
    @namespace "secret"
    function squirrel() {
        return "shhhh"
    }
    @namespace "awk"
    BEGIN {
        exit normal::squirrel()
}""",
    )


def test_cross_namespace_function_calls_3():
    compile_run_answer_assert(
        "shhhh",
        """
    function squirrel() {
        return "squeak"
    }
    @namespace "normal"
    function squirrel() {
        return "tsk"
    }
    @namespace "secret"
    function squirrel() {
        return "shhhh"
    }
    @namespace "awk"
    BEGIN {
        exit secret::squirrel()
}""",
    )


def test_cross_namespace_function_calls_4():
    compile_run_answer_assert(
        "squeak",
        """
    function squirrel() {
        return "squeak"
    }
    @namespace "normal"
    function squirrel() {
        return "tsk"
    }
    @namespace "secret"
    function squirrel() {
        return "shhhh"
    }
    BEGIN {
        exit awk::squirrel()
}""",
    )
