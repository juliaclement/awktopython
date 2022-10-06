#!/usr/bin/python3
"""
    Runtime library for the awk to python translator.
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
from functools import lru_cache  # would rather use @cache, but not available until 3.9
from subprocess import CompletedProcess, Popen, PIPE, TimeoutExpired
from collections import defaultdict
from io import TextIOWrapper
import sys
import re
import subprocess
import os
from pathlib import Path
from awkpy_common import AwkPyArgParser, AwkPySprintfConversion

exit_code = 0


class AwkExit(Exception):
    pass


class AwkNext(Exception):
    pass


class AwkNextFile(Exception):
    pass


class AwkEmptyVar:
    """
    AWK permits a=x+1 and y=x ".tail" when x has not been initialised.
    Python doesn't, nor does it seem to have a built-in type that permits
    it to be treated as both empty string & 0.
    This class might help in simple cases
    """

    def __bool__(self) -> bool:
        return False

    def __int__(self) -> int:
        return 0

    def __float__(self) -> float:
        return 0.0

    def __str__(self) -> str:
        return ""

    def __repr__(self) -> str:
        return "AwkEmptyVar()"

    def __neg__(self) -> int:
        return 0

    def __pos__(self) -> int:
        return 0

    def __abs__(self) -> int:
        return 0

    def __invert__(self) -> int:
        return ~0

    def __eq__(self, anotherObj) -> bool:
        if isinstance(anotherObj, str):
            return anotherObj == ""
        return int(anotherObj) == 0

    def __add__(self, anotherObj):
        return anotherObj

    def __sub__(self, anotherObj):
        return -anotherObj

    def __mul__(self, anotherObj):
        return 0

    def __truediv__(self, anotherObj) -> int:
        return 0

    def __floordiv__(self, anotherObj) -> int:
        return 0

    def __mod__(self, anotherObj) -> int:
        return 0

    def __pow__(self, anotherObj, modulo=None):
        return 0

    def __iadd__(self, anotherObj) -> int:
        return anotherObj

    def __isub__(self, anotherObj) -> int:
        return -anotherObj

    def __imul__(self, anotherObj) -> int:
        return 0

    def __itruediv__(self, anotherObj) -> int:
        return 0

    def __ifloordiv__(self, anotherObj) -> int:
        return 0

    def __imod__(self, anotherObj) -> int:
        return 0

    def __ipow__(self, anotherObj, modulo=None) -> int:
        return 0

    def __ilshift__(self, anotherObj) -> int:
        return 0

    def __irshift__(self, anotherObj) -> int:
        return 0

    def __iand__(self, anotherObj) -> int:
        return 0

    def __ixor__(self, anotherObj) -> int:
        return anotherObj

    def __ior__(self, anotherObj) -> int:
        return anotherObj

    """ These methods are called to implement the binary arithmetic operations (+, -, *, @, /, //, %,
        divmod(), pow(), **, <<, >>, &, ^, |) with reflected (swapped) operands.
        from https://docs.python.org/3/reference/datamodel.html
        For example while AwkEmptyVar + 7 calls __add__, 7 + AwkEmptyVar should call __radd__
    """

    def __radd__(self, anotherObj):
        return anotherObj

    def __rsub__(self, anotherObj):
        return anotherObj

    def __rmul__(self, anotherObj):
        return 0

    # def __rmatmul__(self, anotherObj):
    #    return 0
    def __rtruediv__(self, anotherObj):
        raise ZeroDivisionError  # anotherObj / 0

    def __rfloordiv__(self, anotherObj):
        raise ZeroDivisionError  # anotherObj // 0

    def __rmod__(self, anotherObj):
        raise ZeroDivisionError  # anotherObj % 0

    """
    # I don't think there is an AWK construct that will generate a divmod call
    # so, I've omitted them
    def __divmod__(self, anotherObj):
        return (0,0)
    def __rdivmod__(self, anotherObj):
        raise ZeroDivisionError
    """

    def __rpow__(self, anotherObj, modulo=None):
        return 1

    def __rlshift__(self, anotherObj):
        return anotherObj

    def __rrshift__(self, anotherObj):
        return anotherObj

    def __rand__(self, anotherObj):
        return 0

    def __rxor__(self, anotherObj):
        return anotherObj

    def __ror__(self, anotherObj):
        return anotherObj

    the_instance = None

    @classmethod
    def instance(cls):
        return cls.the_instance


AwkEmptyVar.the_instance = AwkEmptyVar()
AwkEmptyVarInstance = AwkEmptyVar.instance()


class AwkpyRuntimeVarOwner:
    global AwkEmptyVarInstance
    """A class to support translations of AWK variable manipulations
       such as  ++, -- that are not found in Python.
       Used as the base class of AwkpyRuntimeWrapper and directly for 
       owning local variables in translated functions
    """

    def _pre_inc_var(self, varname):
        """self._pre_inc_var('x') implements ++x"""
        try:
            value = getattr(self, varname)
        except:
            value = 0
        value += 1
        setattr(self, varname, value)
        return value

    def _post_inc_var(self, varname):
        """self._post_inc_var('x') implements x++"""
        try:
            value = getattr(self, varname)
        except:
            value = AwkEmptyVarInstance
        setattr(self, varname, value + 1)
        return value

    def _pre_dec_var(self, varname):
        """self._pre_dec_var('x') implements --x"""
        try:
            value = getattr(self, varname)
        except:
            value = 0
        value -= 1
        setattr(self, varname, value)
        return value

    def _post_dec_var(self, varname):
        """self._post_dec_var('x') implements x--"""
        try:
            value = getattr(self, varname)
        except:
            value = AwkEmptyVarInstance
        setattr(self, varname, value - 1)
        return value

    """ As self is never used, the array element versions don't
        need to be in the class.
        I have just placed them here for convenience
    """

    def _pre_inc_arr(self, array: dict, key):
        """self._pre_inc_arr(array,x) implements ++array[x]"""
        value = array.get(
            key, 0
        )  # AWK doc says this should be an empty string, AwkEmptyVarInstance?
        value += 1
        array[key] = value
        return value

    def _pre_dec_arr(self, array: dict, key):
        """self._pre_dec_arr(array,x) implements --array[x]"""
        value = array.get(
            key, 0
        )  # AWK doc says this should be an empty string, AwkEmptyVarInstance?
        value -= 1
        array[key] = value
        return value

    def _post_inc_arr(self, array: dict, key):
        """self._post_inc_arr(array,x) implements array[x]++"""
        value = array.get(
            key, AwkEmptyVarInstance
        )  # AWK doc says this should be an empty string but that can then be treated as 0
        array[key] = value + 1
        return value

    def _post_dec_arr(self, array: dict, key):
        """self._pre_dec_arr(array,x) implements --array[x]"""
        value = array.get(
            key, 0
        )  # AWK doc says this should be an empty string AwkEmptyVarInstance?
        value = array.get(
            key, AwkEmptyVarInstance
        )  # AWK doc says this should be an empty string but that can then be treated as 0
        array[key] = value - 1
        return value

    def _substr(self, string: str, start: int, length: int = None) -> str:
        if start < 1:
            start = 1
        elif start > len(string):
            return ""
        start -= 1  # AWK uses 1 based, Python 0 based
        if length is None:
            return string[start:]
        end = min(start + length, len(string))
        return string[start:end]

    def _to_array(self, list, offset=1):
        """Python has lists & dicts. AWK only has dict like Arrays"""
        ans = defaultdict(AwkEmptyVar, enumerate(list, offset))
        return ans

    def __init__(self):
        pass


class AwkpyRuntimeWrapper(AwkpyRuntimeVarOwner):
    """A class that defines the structure & helper routines
    for the generated Python.
    Translated programs inherit from this class"""

    _ans = 0

    def awkpy__BEGIN(self):
        """
        This method is run before the file input begins.
        It can be used to initialise variables, etc
        """
        pass

    def awkpy__BEGINFILE(self):
        """
        This method is run before each file's input begins.
        It can be used to initialise variables, etc per-file
        """
        pass

    def awkpy__MAINLOOP(self):
        """
        This method is run once for each input line.
        Typically where most of the processing occurs
        """
        pass

    def awkpy__ENDFILE(self):
        """
        This method is run after each file's input ends.
        Typically used for any clean-up and printing per-file summaries.
        """
        pass

    def awkpy__END(self):
        """
        This method is run after all file input ends.
        Typically used for any clean-up and printing summaries.
        """
        pass

    @lru_cache
    def _dynamic_regex(self, regex: str):
        if regex[0] != "(":
            regex = f"({regex})"
        return re.compile(regex)

    def _match(self, haystack, regex_str):
        regex = self._dynamic_regex(regex_str)
        match = regex.search(haystack)
        if match:
            start, end = match.regs[0]
            self.RLENGTH = end - start
            self.RSTART = start + 1
            return self.RSTART
        self.RSTART = self.RLENGTH = -1
        return -1

    def _dynamic_replacement(self, repl: str):
        """Replacement strings in AWK use '&' where Python uses '\1'."""
        # POSIX specifies one \, gawk uses 2 ???
        # I guess this will eventually be reported as a bug
        # meanwhile I'll just brute force it
        repl = repl.replace(r"\\&", chr(1))
        repl = repl.replace(r"\&", chr(1))
        repl = repl.replace("&", r"\1")
        repl = repl.replace(chr(1), r"&")
        return repl

    def _system(self, commandline, capture_output=""):
        opts = {}
        if capture_output != "":
            if capture_output[0] == "$":
                raise ValueError('Can only capture "system" to a normal variable')
            opts["capture_output"] = capture_output
        if self.awkpy__local_environ != 0:
            # need to copy to a fresh dictionary to avoid
            # ValueError: env cannot contain 'PATH' and b'PATH' keys
            env = {k: v for k, v in self.ENVIRON.items()}
            opts["env"] = env
        try:
            completedprocess: CompletedProcess = subprocess.run(
                commandline.split(), encoding="utf-8", **opts
            )
        except FileNotFoundError:
            return -1
        if capture_output != "":
            stdout = (
                ""
                if completedprocess.stdout == ""
                else completedprocess.stdout.strip("\n") + "\n"
            )
            stderr = (
                ""
                if completedprocess.stderr == ""
                else completedprocess.stderr.strip("\n") + "\n"
            )
            self.__setattr__(capture_output, stdout + stderr)
        return completedprocess.returncode

    class FileWrapper:
        def __init__(self, runtime, name: str, mode: str):
            self.runtime: AwkpyRuntimeWrapper = runtime
            self.name = name
            self.mode = mode
            self.rc = 1  # success

        def open(self):
            pass

        def close(self):
            return 0

        def get(self):
            return None

        def print(self, *n, **kw):
            return None

        def get_into_dollar_fields(self):
            self.runtime._set_dollar_fields(self.get())
            return self.rc

        def get_into_dollar_field(self, nr):
            self.runtime._set_dollar_field(nr, self.get())
            return self.rc

        def get_into_variable(self, var):
            self.runtime.__setattr__(var, self.get())
            return self.rc

    class StdInOutWrapper(FileWrapper):
        """Wraps current input file generator & print"""

        def __init__(self, runtime):
            super().__init__(runtime, "", "rw")
            self.file_handle = None

        def open(self):
            pass  # always open

        def get(self):
            try:
                ans = self.runtime._current_input.__next__()
                if ans == "":
                    self.rc = 0
                else:
                    ans = ans.strip("\n")
                    self.rc = 1
            except StopIteration:
                ans = ""
                self.rc = 0
            self.runtime.NR += 1
            self.runtime.FNR += 1
            return ans

        def print(self, *n, **kw):
            print(*n, **kw)

    class FileIOWrapper(FileWrapper):
        def __init__(self, runtime, name: str, mode: str):
            super().__init__(runtime, name, mode)
            self.file_handle = None

        def open(self):
            self.file_handle = open(self.name, self.mode, encoding="utf-8")

        def close(self):
            self.file_handle.close()
            del self.file_handle

        def get(self):
            ans = self.file_handle.readline()
            self.rc = 0 if len(ans) == 0 else 1
            return ans.rstrip()

        def print(self, *n, **kw):
            kw["file"] = self.file_handle
            print(*n, **kw)

    class PipeIOWrapper(FileWrapper):
        def __init__(self, runtime, name: str, mode: str, stdin=None, stdout=None):
            super().__init__(runtime, name, mode)
            self.has_stdin = stdin
            self.has_stdout = stdout
            self.popen = None

        def open(self):
            opts = {}
            if self.has_stdout:
                opts["stdout"] = subprocess.PIPE
            if self.has_stdin:
                opts["stdin"] = subprocess.PIPE
            if self.runtime.awkpy__local_environ != 0:
                # need to copy to a fresh dictionary to avoid
                # ValueError: env cannot contain 'PATH' and b'PATH' keys
                env = {k: v for k, v in self.runtime.ENVIRON.items()}
                opts["env"] = env

            self.popen = subprocess.Popen(self.name.split(), encoding="utf-8", **opts)

        def get(self):
            ans = self.popen.stdout.readline()
            self.rc = 0 if len(ans) == 0 else 1
            return ans.rstrip()

        def print(self, *n, **kw):
            kw["file"] = self.popen.stdin
            print(*n, **kw)

        def close(self):
            if self.popen.stdin:
                self.popen.stdin.close()
            if self.runtime.awkpy__wait_for_pipe_close != 0:
                try:
                    self.popen.wait(2.0)
                except TimeoutExpired:
                    self.popen.kill()
                    self.popen.wait(3.0)
            if self.popen.stdout:
                self.popen.stdout.close()
            del self.popen

    def _access_file(self, name: str, mode: str, stdout=None, stdin=None):
        """Open a file for read or write."""
        try:
            return self._open_files[name]
        except:
            pass
        if "|" in mode:  # ["|r", "|w", '&|'):
            if mode in ["|w", "|"]:
                stdin = True
            if mode in ["|r", "|r", "|"]:
                stdout = True
            if "&" in mode:
                stdin = True
                stdout = True
            the_wrapper = self.PipeIOWrapper(self, name, mode, stdin, stdout)
        elif mode in ["w", "a"]:
            the_wrapper = self.FileIOWrapper(self, name, mode)
        the_wrapper.open()
        self._open_files[name] = the_wrapper
        return the_wrapper

    def _close_file(self, name):
        try:
            the_file = self._open_files[name]
            the_file.close()
            del self._open_files[name]
        except KeyError:  # already closed?
            pass

    def _var_on_commandline(self, opt, arg):
        """implements command line [-v] var=val"""
        optn = opt.split("=", 1)
        setvar = optn[0]
        val = optn[1]

        # gawk accepts -v namespace::name=whatever.
        # now we have implemented namespaces we need to
        # support this, but namespaces are a compile time thing
        # and we don't have access to them here so we just
        # fake it. Probably should move the class involved
        # in managing them somewhere common between us & the
        # compiler but that's a job for another day
        if "::" in setvar:
            optn = setvar.split("::", 1)
            namespace = optn[0]
            setvar = optn[1]
            if namespace != "awk":
                setvar = f"{namespace}__{setvar}"
        # HEURISTIC: if the value is a number, convert it to one
        # Damned if I know if this is the correct thing to do
        # it duplicates what we do in the compiler so if we change
        # one we should change both.
        try:
            value = float(val)
        except:
            value = val
        setattr(self, setvar, value)

    def _format_g(self, raw_value) -> str:
        value = float(raw_value)
        sci_str = f"{value:e}"
        float_str = f"{value}"
        return sci_str if len(sci_str) < len(float_str) else float_str

    def _set_dollar_fields(self, line: str):
        """Set $0 to line, recalculate NF, $1..$NF"""
        if self.FS in [" ", ""]:
            line = line.strip(" \t\n\r")
            FLDS = line.split()
        else:
            line = line.strip("\n\r")
            FLDS = line.split(self.FS)
        self.NF = len(FLDS)
        FLDS = [line] + FLDS
        self._FLDS = defaultdict(AwkEmptyVar, enumerate(FLDS, 0))

    def _set_dollar_field(self, nr, value):
        """Set $nr to value, recalculate $0.
        As value may contain FS, we then
        recalculate the whole $array & NF"""
        if nr == 0:
            self._set_dollar_fields(value)
        else:
            self._FLDS[nr] = value
            sep = " " if self.FS == "" else self.FS
            flds = [v for k, v in self._FLDS.items()]
            line = sep.join(flds[1:])
            self._set_dollar_fields(line)

    def sprintf(self, awk: str, *args: list):
        output = []
        input_field_nr = -1

        while awk != "":
            match = self._sprintf_format_regex.search(awk)
            if not match:
                output.append(awk)
                break
            start, length = match.regs[0]
            if start > 0:
                output.append(awk[:start])
                awk = awk[start:]
                continue
            token = awk[0:length]
            if repl := self._sprintf_replacements.get(token, None):
                output.append(repl)
            elif len(token) < 2:
                print("Ooops got {0}".format(token))
            else:  # %...[letter]
                match = self._sprintf_field_regex.findall(token)
                if match and len(match) > 0:
                    parameter, flags, width, precision, pftype = match[0]
                    parmtype = AwkPySprintfConversion.all_conversions[pftype]
                    # need to process width/precesion before parameter
                    # as they can consume input parameters
                    precision = (
                        parmtype.default_precision if precision == "" else precision
                    )
                    if width != "" or precision != "":
                        if width == "":
                            width = "0"
                        elif width == "*":
                            input_field_nr += 1
                            width = str(int(args[input_field_nr]))
                        if precision != "":
                            precision = precision.lstrip(".")
                            if precision == "*":
                                input_field_nr += 1
                                precision = str(int(args[input_field_nr]))
                            width += "." + precision
                    if parameter == "":
                        input_field_nr += 1
                        param_nr = input_field_nr
                    else:
                        param_nr = int(parameter[0:-1]) - 1
                    paramvalue = parmtype.dynamic(args[param_nr])
                    if len(width) > 0:
                        if "-" in flags:  # left align numbers
                            width = ":<" + width
                        else:
                            width = ":>" + width
                        formatter = "{0" + width + parmtype.format_sfx + "}"
                        token = formatter.format(paramvalue)
                    else:
                        token = str(paramvalue)
                else:
                    print("Internal error, can't refind {token}")
                output.append(token)
            awk = awk[length:]
        return "".join(output)

    def _run(self, argv):
        options = []
        variables = []
        parser = AwkPyArgParser(options, self.ARGV, variables)
        parser.code_found = True  # We are the run-time, not the compiler
        parser.parse(argv)
        for v in variables:
            optn = v[2:]
            self._var_on_commandline(optn, v)
        self.ARGC = len(self.ARGV)
        AwkpyRuntimeWrapper._ans = 0
        """
        Generators to return input lines from stdin & files
        """

        def _get_stdin_slow():
            blocksize = int(self.awkpy__blocksize)
            buffer = sys.stdin.read(blocksize)
            last_pos = len(buffer)
            next_pos = 0
            try:
                while last_pos != 0:
                    try:
                        while next_pos < last_pos:
                            end = buffer.index(self.RS, next_pos)
                            yield buffer[next_pos:end]
                            next_pos = end + 1
                    except ValueError:
                        # record split across blocks, advance
                        # to next block & continue
                        residue = buffer[next_pos:]
                        while residue != "" and len(buffer) > 0:
                            buffer = sys.stdin.read(blocksize)
                            last_pos = len(buffer)
                            end = buffer.find(self.RS)
                            if end < 0:  # not found??? Small buffer?
                                residue += buffer
                            else:
                                yield residue + buffer[:end]
                                residue = ""
                                break
                        if len(residue) > 0:
                            yield residue
                    next_pos = end + 1
                    if next_pos == last_pos and len(buffer) > 0:
                        buffer = sys.stdin.read(blocksize)
                        last_pos = len(buffer)
                        next_pos = 0

            except GeneratorExit:
                pass  # return, ending the generator
            pass  # return, ending the generator

        def _get_stdin():
            self.FNR = 0
            self.FILENAME = "-"
            self._FLDS = []
            self.NF = 0
            if self.awkpy__support_RS == 0:
                self._current_input = sys.stdin
            else:
                self._current_input = _get_stdin_slow()
            self.awkpy__BEGINFILE()
            yield from self._current_input

        def _read_from_file_fast():
            with open(self.FILENAME) as current_file:
                self._current_input = current_file
                yield from current_file

        def _read_from_file_slow():
            blocksize = int(self.awkpy__blocksize)
            with open(self.FILENAME, "r") as current_file:
                self._current_input = current_file
                buffer = current_file.read(blocksize)
                last_pos = len(buffer)
                next_pos = 0
                try:
                    while last_pos != 0:
                        try:
                            while next_pos < last_pos:
                                end = buffer.index(self.RS, next_pos)
                                yield buffer[next_pos:end]
                                next_pos = end + 1
                        except ValueError:
                            # record split across blocks, advance
                            # to next block & continue
                            residue = buffer[next_pos:]
                            while residue != "" and len(buffer) > 0:
                                buffer = current_file.read(blocksize)
                                last_pos = len(buffer)
                                end = buffer.find(self.RS)
                                if end < 0:  # not found??? Small buffer?
                                    residue += buffer
                                else:
                                    yield residue + buffer[:end]
                                    residue = ""
                                    break
                            if len(residue) > 0:
                                yield residue
                        next_pos = end + 1
                        if next_pos == last_pos and len(buffer) > 0:
                            buffer = current_file.read(blocksize)
                            last_pos = len(buffer)
                            next_pos = 0

                except GeneratorExit:
                    pass  # return, ending the generator
                pass  # return, ending the generator

        try:
            self.awkpy__BEGIN()
            if (
                self._has_mainloop
            ):  # only process files and run mainloop if it has some statements
                _, argv = (0, ["-"]) if self.ARGC < 1 else (self.ARGC, self.ARGV)
                for name in argv:
                    self.ARGIND += 1
                    if name[0].isalpha() and "=" in name:
                        self._var_on_commandline(name, name)
                    else:
                        self._FLDS = []
                        self.NF = 0
                        self.FNR = 0
                        self.FILENAME = name
                        if self.FILENAME == "-":
                            self._current_input = _get_stdin()
                        else:
                            if self.awkpy__support_RS == 0:
                                self._current_input = _read_from_file_fast()
                            else:
                                self._current_input = _read_from_file_slow()
                        self.awkpy__BEGINFILE()
                        try:
                            for line in self._current_input:
                                self._set_dollar_fields(line)
                                self.NR += 1
                                self.FNR += 1
                                self.awkpy__MAINLOOP()
                        except AwkNextFile:
                            pass
                        self.awkpy__ENDFILE()
        except AwkExit:
            pass
        try:
            self.awkpy__END()
        except AwkExit:
            pass

        for _, file in self._open_files.items():
            file.close()
        set_exit_code(AwkpyRuntimeWrapper._ans)
        return AwkpyRuntimeWrapper._ans

    def __init__(self):
        super().__init__()
        self.ARGC = 0
        self.ARGV = []
        self.ARGIND = 0
        self.FILENAME = ""
        self.FNR = 0
        self.FS = " "
        self.NF = 0
        self.NR = 0
        self.OFS = " "
        self.ORS = "\n"
        self.RLENGTH = AwkEmptyVar.instance
        self.RSTART = AwkEmptyVar.instance
        self.RS = "\n"
        self.CONVFMT = "%.6g"
        self.OFMT = "%.6g"
        self.ENVIRON = defaultdict(AwkEmptyVar.instance, os.environ)
        #
        # awkpy namespace
        #
        self.awkpy__wait_for_pipe_close = 0  # (False)
        self.awkpy__support_RS = 1  # (True)
        self.awkpy__blocksize = -1  # (Read whole file)
        self.awkpy__local_environ = 1  # (True)

        # files open for input or output
        self._std_in_out = self.StdInOutWrapper(self)
        self._open_files = {
            "": self._std_in_out
        }  # and anything else the awk code opens
        # if no statements are present in the main loop,
        # input files are not processed
        self._has_mainloop = False
        # used by sprintf
        self._sprintf_require_int = AwkPySprintfConversion.all_conversions["d"]
        fieldspec = (
            r"([0-9]*\$)?([-+ 0'#])?([1-9*][0-9]*)?([.][0-9*]+)?([aAcdeEfFgGiosuxX])"
        )
        self._sprintf_field_regex = re.compile(fieldspec)
        self._sprintf_format_regex = re.compile(r"([\\%]%)|([{}])|(%" + fieldspec + ")")
        self._sprintf_replacements = {r"\%": "%", "%%": "%", "{": "{", "}": "}"}


def set_exit_code(code):
    global exit_code
    exit_code = code
