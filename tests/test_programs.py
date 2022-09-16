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
from awkpy_compiler import AwkPyCompiler
from helpers import full_file_name, Fuzzy
import awkpy
import awkpycc

def check_compile_to_disk(compiler, filename, value, check, args:list):
    if isinstance( args, str):
        args=[args]
    if filename:
        extras=["program", "-o", str(filename)]
    else:
        extras=["program"]
    extras.extend(args)
    compiler(extras)
    if filename:
        with open(filename, 'r') as f:
            text = f.read()
        assert check(value,text)

def test_compile_to_disk(tmp_path):
    source_out=tmp_path / 'compile_to_disk.py'
    checker=lambda value,txt: value in txt
    check_compile_to_disk(awkpycc.run, source_out, 'AwkPyTranslated',  checker, '''function fnord() {
    print "fnords."
}
BEGIN {
    fnord()
}''')

def test_compile_to_disk_and_run(tmp_path):
    source_out=tmp_path / 'compile_to_disk_and_run.py'
    checker=lambda value,txt: value in txt
    check_compile_to_disk(awkpy.run, source_out, 'AwkPyTranslated',  checker, ['-d','''function fnord() {
    print "fnords."
}
BEGIN {
    fnord()
}'''])

def test_compile_not_to_disk(tmp_path):
    source_out=None
    checker=lambda value,txt: value in txt
    check_compile_to_disk(awkpycc.run, source_out, 'AwkPyTranslated',  checker, ['-d','''function fnord() {
    print "fnords."
}
BEGIN {
    fnord()
}'''])

def test_compile_not_to_disk_and_run(tmp_path):
    source_out=None
    checker=lambda value,txt: value in txt
    check_compile_to_disk(awkpy.run, source_out, 'AwkPyTranslated',  checker, ['-d','''function fnord() {
    print "fnords."
}
BEGIN {
    fnord()
}'''])

def test_Wr_option(capsys):
    awkpy.run(['awkpy_out','-vA=Z', '-v', 'C=Y', 'BEGIN {print "A="A", C="C;}','-Wr','-vA=B', '-v', 'C=D'])
    captured = capsys.readouterr()
    assert captured.out == 'A=B, C=D\n'

def test_use_stdin_if_no_files(capsys, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO('my input'))
    awkpy.run(['awkpy_out','{print $1}'])
    captured = capsys.readouterr()
    assert captured.out == 'my\n'

def test_use_stdin_mixed_with_files(capsys, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO('Line.4 ++'))
    file=str(full_file_name('lines.txt'))
    awkpy.run(['awkpy_out','$1=="Line.4"{print $2}',file,'-'])
    captured = capsys.readouterr()
    assert captured.out == "--\n++\n"

def test_use_var_between_files(capsys):
    file=str(full_file_name('lines.txt'))
    awkpy.run(['awkpy_out','-v', 'A=File.1', '$1=="Line.4"{print A","$1}',file, 'A=File.2', file])
    captured = capsys.readouterr()
    assert captured.out == "File.1,Line.4\nFile.2,Line.4\n"

def test_use_stdin_ahead_of_files(capsys, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO('Line.4 ++'))
    file=str(full_file_name('lines.txt'))
    awkpy.run(['awkpy_out','$1=="Line.4"{print $2}','-',file])
    captured = capsys.readouterr()
    assert captured.out == "++\n--\n"

if __name__=="__main__":     awkpy.run(['awkpy_out','-vA=Z', '-v', 'B=Y', 'BEGIN {print "A="A", B="B;}','-Wr','-vA=B', '-v', 'C=D'])
