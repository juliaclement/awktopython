#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
""" AWK - Python translator tests
    test the front end programs  """
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
from helpers import full_file_name, Fuzzy

try:
    import awkpy
except:
    path = Path(__file__).parent.parent / "code"
    sys.path.append(str(path))
    import awkpy

import awkpycc
from awkpy_runtime import AwkpyRuntimeWrapper
from awkpy_compiler import AwkPyCompiler


def check_compile_to_disk(compiler, filename, value, check, args: list):
    if isinstance(args, str):
        args = [args]
    if filename:
        extras = ["program", "-o", str(filename)]
    else:
        extras = ["program"]
    extras.extend(args)
    compiler(extras)
    if filename:
        with open(filename, "r") as f:
            text = f.read()
        assert check(value, text)


def test_compile_to_disk(tmp_path):
    source_out = tmp_path / "compile_to_disk.py"
    checker = lambda value, txt: value in txt
    check_compile_to_disk(
        awkpycc.run,
        source_out,
        "AwkPyTranslated",
        checker,
        """function fnord() {
    print "fnords."
}
BEGIN {
    fnord()
}""",
    )


def test_compile_to_disk_and_run(tmp_path):
    source_out = tmp_path / "compile_to_disk_and_run.py"
    checker = lambda value, txt: value in txt
    check_compile_to_disk(
        awkpy.run,
        source_out,
        "AwkPyTranslated",
        checker,
        [
            "-d",
            """function fnord() {
    print "fnords."
}
BEGIN {
    fnord()
}""",
        ],
    )


def test_compile_not_to_disk(tmp_path):
    source_out = None
    checker = lambda value, txt: value in txt
    check_compile_to_disk(
        awkpycc.run,
        source_out,
        "AwkPyTranslated",
        checker,
        [
            "-d",
            """function fnord() {
    print "fnords."
}
BEGIN {
    fnord()
}""",
        ],
    )


def test_compile_not_to_disk_and_run(tmp_path):
    source_out = None
    checker = lambda value, txt: value in txt
    check_compile_to_disk(
        awkpy.run,
        source_out,
        "AwkPyTranslated",
        checker,
        [
            "-d",
            """function fnord() {
    print "fnords."
}
BEGIN {
    fnord()
}""",
        ],
    )


def test_namespace_awk_compiler(capsys):
    awkpy.run(
        ["awkpy_out", "-vawk::a=Z", "-v", "awk::c=Y", 'BEGIN {print "A="a", C="c;}']
    )
    captured = capsys.readouterr()
    assert captured.out == "A=Z, C=Y\n"


def test_namespace_awk_runtime(capsys):
    awkpy.run(
        [
            "awkpy_out",
            "-vawk::A=Z",
            "-v",
            "awk::C=Y",
            'BEGIN {print "A="A", C="C;}',
            "-Wr",
            "-vawk::A=B",
            "-v",
            "awk::C=D",
        ]
    )
    captured = capsys.readouterr()
    assert captured.out == "A=B, C=D\n"


def test_namespace_user_compiler(capsys):
    awkpy.run(
        [
            "awkpy_out",
            "-vuser::a=Z",
            "-v",
            "user::c=Y",
            'BEGIN {print "A="user::a", C="user::c;}',
        ]
    )
    captured = capsys.readouterr()
    assert captured.out == "A=Z, C=Y\n"


def test_namespace_user_runtime(capsys):
    awkpy.run(
        [
            "awkpy_out",
            "-vuser::a=Z",
            "-v",
            "user::c=Y",
            'BEGIN {print "A="user::a", C="user::c;}',
            "-Wr",
            "-vuser::a=B",
            "-v",
            "user::c=D",
        ]
    )
    captured = capsys.readouterr()
    assert captured.out == "A=B, C=D\n"


def test_minus_F(capsys,monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("a@b cd"))
    awkpy.run(
        [
            "awkpy_out",
            "-F@",
            "-vOFS=%",
            '{print $1,$2}'
        ]
    )
    captured = capsys.readouterr()
    assert captured.out == "a%b cd\n"


def test_minus_F_runtime(capsys,monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("a@b cd"))
    awkpy.run(
        [
            "awkpy_out",
            '{print $1,$2}',
            "-Wr",
            "-F@",
            "-vOFS=%"
        ]
    )
    captured = capsys.readouterr()
    assert captured.out == "a%b cd\n"


def test_Wr_option(capsys):
    awkpy.run(
        [
            "awkpy_out",
            "-vA=Z",
            "-v",
            "C=Y",
            'BEGIN {print "A="A", C="C;}',
            "-Wr",
            "-vA=B",
            "-v",
            "C=D",
        ]
    )
    captured = capsys.readouterr()
    assert captured.out == "A=B, C=D\n"


def test_use_stdin_if_no_files(capsys, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("my input"))
    awkpy.run(["awkpy_out", "{print $1}"])
    captured = capsys.readouterr()
    assert captured.out == "my\n"


def test_use_stdin_mixed_with_files(capsys, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("Line.4 ++"))
    file = str(full_file_name("lines.txt"))
    awkpy.run(["awkpy_out", '$1=="Line.4"{print $2}', file, "-"])
    captured = capsys.readouterr()
    assert captured.out == "--\n++\n"


def test_use_var_between_files(capsys):
    file = str(full_file_name("lines.txt"))
    awkpy.run(
        [
            "awkpy_out",
            "-v",
            "A=File.1",
            '$1=="Line.4"{print A","$1}',
            file,
            "A=File.2",
            file,
        ]
    )
    captured = capsys.readouterr()
    assert captured.out == "File.1,Line.4\nFile.2,Line.4\n"


def test_use_namespace_var_between_files(capsys):
    file = str(full_file_name("lines.txt"))
    awkpy.run(
        [
            "awkpy_out",
            "-v",
            "A=File.1",
            '$1=="Line.4"{print A","$1}',
            file,
            "awk::A=File.2",
            file,
        ]
    )
    captured = capsys.readouterr()
    assert captured.out == "File.1,Line.4\nFile.2,Line.4\n"


def test_use_stdin_ahead_of_files(capsys, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("Line.4 ++"))
    file = str(full_file_name("lines.txt"))
    awkpy.run(["awkpy_out", '$1=="Line.4"{print $2}', "-", file])
    captured = capsys.readouterr()
    assert captured.out == "++\n--\n"


def test_f_includes_files_twice():
    path = Path(__file__).parent.parent / "tests"
    file = str(path / "add_1_in_BEGIN.awk")
    awkpy.run(["awkpy_out", "-f", file, "-f", file, "-e", "BEGIN {exit a;}"])
    assert AwkpyRuntimeWrapper._ans == 2


def test_i_includes_files_once():
    path = Path(__file__).parent.parent / "tests"
    file = str(path / "add_1_in_BEGIN.awk")
    awkpy.run(["awkpy_out", "-i", file, "-i", file, "-e", "BEGIN {exit a;}"])
    assert AwkpyRuntimeWrapper._ans == 1


def test_i_precludes_f():
    path = Path(__file__).parent.parent / "tests"
    file = str(path / "add_1_in_BEGIN.awk")
    try:
        assert (
            awkpy.run(["awkpy_out", "-i", file, "-f", file, "-e", "BEGIN {exit a;}"])
            is False
        )
    except SyntaxError as err:
        print(f"Error: {err}")


def test_f_precludes_i():
    path = Path(__file__).parent.parent / "tests"
    file = str(path / "add_1_in_BEGIN.awk")
    try:
        assert (
            awkpy.run(["awkpy_out", "-f", file, "-i", file, "-e", "BEGIN {exit a;}"])
            is False
        )
    except SyntaxError as err:
        print(f"Error: {err}")


def test_include_includes_file():
    path = Path(__file__).parent.parent / "tests"
    file = str(path / "add_1_in_BEGIN.awk")
    awkpy.run(
        [
            "awkpy_out",
            '@include "'
            + file
            + '"\
    BEGIN {exit a;}',
        ]
    )
    assert AwkpyRuntimeWrapper._ans == 1


def test_include_starts_in_awk_ns():
    # also tests that namespace is restored on exit from the include
    path = Path(__file__).parent.parent / "tests"
    file = str(path / "add_1_in_BEGIN.awk")
    awkpy.run(
        [
            "awkpy_out",
            '''BEGIN {
        @namespace "q"
        a=7;}
    @include "'''
            + file
            + """"
    BEGIN {
        exit a;}""",
        ]
    )
    assert AwkpyRuntimeWrapper._ans == 7


def test_include_and_i_mutually_block_includes_file():
    path = Path(__file__).parent.parent / "tests"
    file = str(path / "add_1_in_BEGIN.awk")
    awkpy.run(
        [
            "awkpy_out",
            "-i",
            file,
            "-e",
            '@include "'
            + file
            + '"\
    BEGIN {exit a;}',
        ]
    )
    assert AwkpyRuntimeWrapper._ans == 1


def test_include_includes_file_only_once():
    path = Path(__file__).parent.parent / "tests"
    file = str(path / "add_1_in_BEGIN.awk")
    awkpy.run(
        [
            "awkpy_out",
            '@include "'
            + file
            + '"\
    @include "'
            + file
            + '"\
    BEGIN {exit a;}',
        ]
    )
    assert AwkpyRuntimeWrapper._ans == 1


if __name__ == "__main__":
    awkpy.run(
        [
            "awkpy_out",
            "-vA=Z",
            "-v",
            "B=Y",
            'BEGIN {print "A="A", B="B;}',
            "-Wr",
            "-vA=B",
            "-v",
            "C=D",
        ]
    )

test_i_precludes_f()
test_f_precludes_i()
