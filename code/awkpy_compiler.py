#!/usr/bin/python3
"""
    compiler for the awk to python translator.
    requires a wrapper to supply lines and either save or run the
    generated python
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

from curses.ascii import isupper
import re
from enum import IntEnum
from collections import defaultdict
from tarfile import SYMTYPE

""" Helper classes"""
""" Namespaces """


class AwkNamespace:
    awk_namespaces = {}
    awk_current_namespace = None
    awk_awk_namespace = None
    awk_awkpy_namespace = None

    @classmethod
    def get_current_namespace(cls):
        return cls.awk_current_namespace

    @classmethod
    def set_current_namespace(cls, namespace):
        prior_namespace = cls.awk_current_namespace
        if isinstance(namespace, AwkNamespace):
            ns = namespace
        else:
            ns = AwkNamespace.awk_namespaces.get(namespace, None)
            if ns is None:
                ns = AwkNamespace(namespace)
        cls.awk_current_namespace = ns
        return prior_namespace

    @classmethod
    def startup(cls):
        # to avoid polluting the global namespace, awkpy is where any of our own
        # extensions will go. For example the routine to convert Python lists to
        # AWK style arrays will eventually be moved in there
        cls.awk_awkpy_namespace = AwkNamespace("awkpy")
        # The awk namespace is a bit magic, it does not impose a prefix
        # on symbols defined in it
        cls.awk_awk_namespace = cls.awk_current_namespace = AwkNamespace(
            "awk", "self.", ""
        )

    @classmethod
    def get_namespace(cls, ns_name):
        ns = cls.awk_namespaces.get(ns_name, None)
        if ns is None:
            ns = AwkNamespace(ns_name)
        return ns

    @classmethod
    def find_ns(cls, varname: str):
        if "::" in varname:
            parts = varname.split("::")
            ns_name = parts[0]
            return cls.get_namespace(ns_name)
        if varname.isupper():
            return cls.awk_awk_namespace
        return cls.awk_current_namespace

    def __init__(self, name, python_equivalent=None, decorated=None):
        # There can only be one instance for any namespace name
        # Don't allow synonyms to override any changes
        if not name in self.awk_namespaces:
            self.name = name
            self.python_equivalent = (
                "self." + name + "__"
                if python_equivalent is None
                else python_equivalent
            )
            self.decorated = name + "::" if decorated is None else decorated
            AwkNamespace.awk_namespaces[name] = self

    #
    # There can only be one instance for any namespace name
    #
    def __new__(cls, name, *args, **kw):
        if name in cls.awk_namespaces:
            return cls.awk_namespaces[name]
        return super().__new__(cls)


AwkNamespace.startup()

""" Symbol Table"""


class SymType(IntEnum):
    UNKNOWN = 0  # Unknown
    NONE = 1  # None
    SPACE = 2  # Space
    VARIABLE = 3  # Variable
    NUMBER = 4  # Number
    BINOPERATOR = 5  # Binary_operator
    UNIOPERATOR = 6  # Unary_operator
    AMBIGUOUSOPERATOR = 7  # Operator
    LEFT_BRACKET = 8  # [
    RIGHT_BRACKET = 9  # ]
    LEFT_PAREN = 10  # (
    RIGHT_PAREN = 11  # )
    LEFT_BRACE = 12  # {
    RIGHT_BRACE = 13  # }
    RESERVED_WORD = 14  # Reserved_word
    DOLLAR = 15  # $
    STRING = 16  # String
    FUNCTION = 17  # A_function
    SECTION = 18  # A_section
    STATEMENT = 19  # A_statement
    COMMA = 20  # Comma
    REGEX = 20  # Regex
    STATEMENT_TERMINATOR = 22  # Terminator
    END_OF_INPUT = 23  # End_Of_Input


#   Sym
sym_display_name = [
    "Unknown",
    "None",
    "Space",
    "Variable",
    "Number",
    "Binary_operator",
    "Unary_operator",
    "Operator",
    "[",
    "]",
    "(",
    ")",
    "{",
    "}",
    "Reserved_word",
    "$",
    "String",
    "A_function",
    "A_section",
    "A_statement",
    "Comma",
    "Regex",
    "Terminator",
    "End_Of_Input",
]
#   Created from above by the command
#   awk 'BEGIN {reject=1;prinf("sym_display_name=[  ")} $2~/SymType/ {reject=0;next} $2~/Sym/ {print "                 ";exit} reject==0 { print "                    \""$5"\","}' awkpy_compiler.py


class Sym:
    """Symbol table entry"""

    def __init__(
        self,
        token: str,
        sym_type: SymType = SymType.NONE,
        awk_priority: int = 10000,
        python_priority: int = 10000,
        python_equivalent=None,
    ):
        self.token = token
        self.sym_type = sym_type
        self.awk_priority = awk_priority
        self.python_priority = python_priority
        self.python_equivalent = (
            token if python_equivalent is None else python_equivalent
        )
        self.init = "AwkEmptyVarInstance"

    def is_operator(self):
        return self.sym_type in [
            SymType.BINOPERATOR,
            SymType.UNIOPERATOR,
            SymType.AMBIGUOUSOPERATOR,
            SymType.LEFT_BRACKET,
        ]

    def is_operand(self):
        return self.sym_type in [
            SymType.VARIABLE,
            SymType.DOLLAR,
            SymType.NUMBER,
            SymType.STRING,
            SymType.FUNCTION,
            SymType.RIGHT_BRACKET,
            SymType.RIGHT_PAREN,
        ]  # ,SymType.LEFT_PAREN

    def is_function(self):
        return False

    def is_terminator(self):
        return False

    def is_variable(self):
        return self.sym_type == SymType.VARIABLE

    def is_regex(self):
        return False


class SymOperator(Sym):
    """Symbol table entry for operators"""

    def __init__(
        self,
        token: str,
        sym_type: SymType = SymType.NONE,
        awk_priority: int = 10000,
        python_priority: int = 10000,
        python_equivalent=None,
    ):
        super().__init__(
            token, sym_type, awk_priority, python_priority, python_equivalent
        )

    def is_operator(self):
        return True


class SymRegex(Sym):
    """Symbol table entry for regular expressions"""

    def __init__(
        self,
        token: str,
        sym_type: SymType = SymType.REGEX,
        awk_priority: int = 10000,
        python_priority: int = 10000,
        python_equivalent=None,
    ):
        super().__init__(
            token, sym_type, awk_priority, python_priority, python_equivalent
        )

    def is_operand(self):
        return True

    def is_regex(self):
        return True


class SymVariable(Sym):
    """Symbol table entry for variable, build-in or user defined"""

    def __init__(
        self,
        token: str,
        sym_type: SymType = SymType.VARIABLE,
        awk_priority: int = 10000,
        python_priority: int = 10000,
        python_equivalent=None,
        built_in=False,
        array=False,
        scalar=False,
    ):
        if python_equivalent is None:
            python_equivalent = "self." + token.replace("::", "__")
        super().__init__(
            token, sym_type, awk_priority, python_priority, python_equivalent
        )
        self.built_in = built_in
        self.is_array = array
        self.is_scalar = scalar

    def is_operator(self):
        return False

    def is_operand(self):
        return True

    def is_variable(self):
        return True

    def is_built_in(self):
        return self.built_in


class SymBinaryOperator(SymOperator):
    """Symbol table entry for operators"""

    def __init__(
        self,
        token: str,
        sym_type: SymType = SymType.BINOPERATOR,
        awk_priority: int = 10000,
        python_priority: int = 10000,
        python_equivalent=None,
    ):
        super().__init__(
            token, sym_type, awk_priority, python_priority, python_equivalent
        )


class SymUnaryOperator(SymOperator):
    """Symbol table entry for operators"""

    def __init__(
        self,
        token: str,
        sym_type: SymType = SymType.UNIOPERATOR,
        awk_priority: int = 10000,
        python_priority: int = 10000,
        python_equivalent=None,
    ):
        super().__init__(
            token, sym_type, awk_priority, python_priority, python_equivalent
        )


class SymAmbiguous(SymOperator):
    """Symbol table entry for operators that may be either unary or binary"""

    def __init__(self, uni_op: Sym, bin_op: Sym, token=None):
        self.bin_op = bin_op
        self.uni_op = uni_op
        if token is None:
            token = bin_op.token if uni_op.token is None else uni_op.token
        super().__init__(
            token, SymType.AMBIGUOUSOPERATOR, python_equivalent=bin_op.python_equivalent
        )

    def is_operator(self):
        return False

    def is_operand(self):
        return True

    def unary_op(self):
        return self.uni_op

    def binary_op(self):
        return self.bin_op


default_function_parser = None
default_function_method_parser = None


class SymFunction(Sym):
    """Symbol table entry for functions, built-in and user defined"""

    def __init__(
        self,
        token: str,
        parser=None,
        python_equivalent=None,
        user_defined=False,
        ext_library=None,
    ):
        global default_function_parser
        self.user_defined = user_defined
        if user_defined and python_equivalent is None:
            python_equivalent = "self." + token.replace("::", "__")
        super().__init__(token, SymType.FUNCTION, python_equivalent=python_equivalent)
        if (
            ext_library is None
            and not user_defined
            and python_equivalent is not None
            and "." in python_equivalent
        ):
            ext_library = python_equivalent.split(".")[0]
        if ext_library is None or ext_library == "self":
            self.ext_library = None
        else:
            self.ext_library = ext_library
        self.parser = default_function_parser if parser is None else parser

    def parse(self):
        self.parser()

    def is_function(self):
        return True

    def is_operator(self):
        return False

    def is_operand(self):
        return True


class SymStatement(Sym):
    """Symbol table entry for statement keywords"""

    def __init__(self, token: str, parser, python_equivalent=None):
        super().__init__(token, SymType.STATEMENT, python_equivalent=python_equivalent)
        self.parser = parser

    def parse(self):
        self.parser()

    def is_operator(self):
        return False

    def is_operand(self):
        return False


class SymTerminator(Sym):
    """Symbol table entry for functions, built-in and user defined"""

    def __init__(
        self, token: str, consume: bool, multiples_are_one: bool, python_equivalent=None
    ):
        super().__init__(
            token, SymType.STATEMENT_TERMINATOR, python_equivalent=python_equivalent
        )
        self.multiples_are_one = multiples_are_one
        self.consume = consume

    def is_operator(self):
        return False

    def is_operand(self):
        return False

    def is_terminator(self):
        return True


class AwkPyCompiler:
    """This is the main class of the compiler"""

    def syntax_error(self, expected):
        """ "Used by the parser to report syntax errors"""
        locate = ""
        point = max(0, self.current_token_nr - 4)
        while point < self.current_token_nr:
            locate += self.tokens[point][1].token + " "
            point += 1
        locate += ">>>" + self.current_token.token + "<<< "
        point += 1
        while point < min(len(self.tokens), self.current_token_nr + 4):
            locate += self.tokens[point][1].token + " "
            point += 1
        raise SyntaxError(
            f'Found "{self.current_token.token}" expected {expected} "+\
                           f"near {locate}- token {self.current_token_nr} which is on line {self.current_line}'
        )

    def lex_lines(self, lines_arr: list, filename):
        line_nr = 0
        yield f"@file {filename}"
        while line_nr < len(lines_arr):
            line = lines_arr[line_nr].strip()
            yield f"@@@{line_nr}@@@{line}"
            expect_namespace = False
            expect_filename = False
            while line:
                if match := self.lexre.search(line):
                    start, length = match.regs[0]
                    if start > 0:
                        if line[0] == " ":
                            line = line.strip()
                            continue
                        yield line[:start]
                        line = line[start:]
                        continue
                    token = line[:length]
                    line = line[length:]
                    # we handle selecting namespaces very early as they permute the
                    # internal naming of variables & other symbols
                    if expect_namespace:
                        expect_namespace = False
                        token = token.strip('"')
                        AwkNamespace.set_current_namespace(token)
                        yield f'@namespace "{token}"'
                        continue
                    elif token == "@namespace":
                        expect_namespace = True
                        continue
                    # @include also handled early to reduce complexity
                    # in our caller
                    if expect_filename:
                        expect_filename = False
                        inner_filename = token.strip('"')
                        if inner_filename in self.source_files:
                            raise SyntaxError(
                                f"{inner_filename} can't be used as both included and as a source file "
                            )
                        if inner_filename in self.included_files:
                            continue
                        self.included_files.append(inner_filename)
                        file = open(inner_filename, mode="r")
                        source = file.read()
                        file.close()
                        oldns = AwkNamespace.set_current_namespace(
                            AwkNamespace.awk_awk_namespace
                        )
                        yield f'@namespace "{AwkNamespace.awk_awk_namespace.name}"'
                        yield from self.lex_lines(source.split("\n"), inner_filename)
                        yield f'@resuming "{filename}"'
                        AwkNamespace.set_current_namespace(oldns)
                        yield f'@namespace "{oldns.name}"'
                        continue
                    elif token == "@include":
                        expect_filename = True
                        continue
                    # Because of the ambiguity of detecting them, our regex
                    # has additional characters prepended to regexes.
                    is_prefixed_regex = token[0] in "!~(," and "/" in token
                    # strings and regexs may span multiple lines
                    if (
                        (token[0] in "\"'" and token[-1] != token[0])
                        or (is_prefixed_regex or token[0] == "/")
                        and token[-1] != "/"
                    ):
                        if token[-1] == "\\":
                            token = token[:-1]
                        line_nr += 1
                        if line_nr < len(lines_arr):
                            line += token + lines_arr[line_nr]
                            yield f"@@@{line_nr}@@@{line}"
                            continue
                    # now is the time to split prepended characters from regexes
                    if is_prefixed_regex:
                        toks = token.split("/", 1)
                        yield toks[0].strip()
                        token = "/" + toks[1]
                    yield token
                else:
                    yield line
                    break
            yield "\n"
            line_nr += 1

    def lex_string(self, filename, source):
        """Walk through the raw tokens produced by calls to self.lex
        converting them into symbol table entries.
        The input line number is stored with each cooked token"""
        oldns = AwkNamespace.set_current_namespace(AwkNamespace.awk_awk_namespace)
        answer = []
        sym_lf = self.syms.get("\n")
        sym = sym_lf
        have_output = False
        if isinstance(source, str):
            source = source.split("\n")
        for token in self.lex_lines(source, filename):
            if len(token) > 1:
                token = token.strip()
            if len(token) > 2 and token.startswith("@@@"):
                sym = sym_lf
                self.lineNr += 1
                have_output = False
                continue  # line number
            if (
                token.startswith("@namespace")
                or token.startswith("@file")
                or token.startswith("@resuming")
            ):
                continue  # I doubt it's needed later
            # decorate identifiers for the current namespace unless disallowed.
            # NB ns::name fails the isidentifier test so needs special processing
            tokenns = AwkNamespace.awk_current_namespace
            if "::" in token and token.replace("::", "__").isidentifier():
                tokparts = token.split("::", 1)
                tokenns = AwkNamespace.get_namespace(tokparts[0])
                token = tokparts[1]
            if (
                token.isidentifier()
                and not token.isupper()
                and token not in self.reserved_words
            ):
                token = tokenns.decorated + token

            sym = self.syms.get(token)
            if sym is None:
                if token[0] in "1234567890":
                    sym = Sym(token, SymType.NUMBER)
                elif token.replace("::", "__").isidentifier():
                    sym = SymVariable(token)
                elif token[0] == '"':
                    sym = Sym(token.replace(chr(1), '\\"'), SymType.STRING)
                elif token[0].isspace():
                    # sym=Sym(token,SymType.SPACE)
                    continue
                elif token[0] == ",":
                    sym = Sym(token, SymType.COMMA)
                elif len(token) > 1 and token[0] == "-" and token[1] in "1234567890":
                    sym = Sym(token, SymType.NUMBER)
                elif len(token) > 1 and token[0] == "$":
                    sym = Sym(
                        token,
                        SymType.DOLLAR,
                        python_equivalent=f"self._FLDS[{token[1:]}]",
                    )
                elif (
                    len(token) > 1 and token[0] == "/"
                ):  # regex, operators already recognised
                    sym = SymRegex(token)
                else:
                    raise NameError(
                        f"Unrecognised token {token} near line {self.lineNr}"
                    )
                self.syms[token] = sym
            if have_output or sym.token != "\n":
                answer.append((self.lineNr, sym))
                have_output = True
            # if sym.sym_type not in [ SymType.STATEMENT_TERMINATOR, SymType.LEFT_BRACE ]:
            #    answer.append( (self.lineNr, sym_lf) )
        sym = (-1, Sym("EndOfInput", SymType.END_OF_INPUT))
        answer.append(sym)
        answer.append(sym)
        answer.append(sym)
        AwkNamespace.set_current_namespace(oldns)
        return answer

    def advance_token(self):
        """Expose the current token, as well as the prior and next tokens
        to the parser.
        This is the interface between the lexer & the parser
        """
        self.prior_token = self.current_token
        self.current_token_nr += 1
        self.current_line = self.lookahead_line
        self.current_token = self.lookahead_token
        if self.current_token_nr + 1 < len(self.tokens):
            self.lookahead_line, self.lookahead_token = self.tokens[
                self.current_token_nr + 1
            ]
            self.lookahead_token = self.replacement_syms.get(
                self.lookahead_token.token, self.lookahead_token
            )

    def advance_token_require(self, tokens=None, sym_types: list = None):
        """Get the next token, and check it is in a valid list"""
        self.advance_token()
        if sym_types and self.current_token.sym_type in sym_types:
            return
        if tokens and self.current_token.token in tokens:
            return
        if tokens is None:
            tokens = []
        if sym_types is not None:
            t: SymType
            for t in sym_types:
                tokens.append(sym_display_name[t])
        self.syntax_error(", ".join(tokens))

    def consume_terminator(self):
        multiples = self.current_token.multiples_are_one
        if self.current_token.consume:
            self.advance_token()
            if (
                multiples
                and self.current_token.sym_type == SymType.STATEMENT_TERMINATOR
            ):
                target = self.current_token.token
                while self.lookahead_token.token == target:
                    self.advance_token()

    """Output the generated Python code"""

    def start_defer_output(self):
        """Suport do {} while( condition) by allowing the body of the do
        to be processed as usual, then be extracted and wrapped
        in the generated conditional code"""
        old_output = self.generated_code[self.current_output]
        self.generated_code[self.current_output] = []
        return old_output

    def end_deferred_output(self, replacement):
        """End of the deferred output begin by start_defer_output
        NB: start_deferred_output === end_deferred_output([]) MERGE?"""
        old_output = self.generated_code[self.current_output]
        self.generated_code[self.current_output] = replacement
        return old_output

    def output_block(self, block):
        """Used t oreinsert the code removed by end_deferred_output"""
        self.generated_code[self.current_output].extend(block)

    def output_line(self, line):
        """Output a single line"""
        self.generated_code[self.current_output].append(self.indent + line)

    """Expressions & conditions"""

    def compile_regex(self, variable, test):
        """pattern match variable against next"""
        pfx, sfx = (" not (", ")") if test == "!~" else (" ", "")
        pattern = ""
        if self.current_token.token[0] != "/" and not self.current_token.is_regex():
            self.advance_token()  # get rid of operator
        if self.current_token.is_regex():
            pattern = self.current_token.token[1:-1]
        elif self.current_token.is_variable():
            return (
                pfx
                + f"re.search({self.current_token.python_equivalent},str({variable}))"
                + sfx
            )
        else:
            if self.current_token.token != "/":
                self.syntax_error("/")
            self.advance_token()
            while self.current_token.token != "/":
                pattern += self.current_token.token
                self.advance_token()
        return pfx + f're.search(r"{pattern}",str({variable}))' + sfx

    def compile_uni_operator(self, ans: list = []) -> list:
        if self.current_token.token in ["++", "--"]:  # pre_inc / pre_dec
            op = self.current_token.token
            self.advance_token_require(sym_types=[SymType.VARIABLE])
            var = self.current_token
            var_parts = var.python_equivalent.split(".", 1)
            if self.lookahead_token.token == "[":
                self.advance_token()
                op_fun = "_pre_inc_arr" if op == "++" else "_pre_dec_arr"
                self.advance_token()
                index = self.compile_expression()
                ans.append(f"{var_parts[0]}.{op_fun}({var.python_equivalent},{index})")
            else:
                op_fun = "_pre_inc_var" if op == "++" else "_pre_dec_var"
                ans.append(f"{var_parts[0]}.{op_fun}('{var_parts[1]}')")
            self.advance_token()
        elif self.current_token.sym_type in [
            SymType.AMBIGUOUSOPERATOR,
            SymType.UNIOPERATOR,
        ]:
            # - ++ -- ...
            ans.append(self.current_token.python_equivalent)
            self.advance_token()
        else:
            self.syntax_error("operand or unary operator")
        return ans

    def parse_gather_function_args(self, terminators, discard_opening_parenthesis):
        args = []
        if discard_opening_parenthesis:
            self.advance_token_require(["("])
            self.advance_token()  # Discard ( or comma
        while self.current_token.sym_type not in terminators:
            args.append(self.compile_expression([SymType.COMMA]))
            if self.current_token.sym_type == SymType.COMMA:
                self.advance_token()  # Discard comma
        return args

    def compile_function_call_to_method(self, terminators=[], offset=False):
        """Compile fn([a [, b]]...) to a.fn([b...])"""
        fn = self.current_token
        args = self.parse_gather_function_args(
            terminators + [SymType.RIGHT_PAREN], True
        )
        var = args[0]
        if len(args) > 1:
            args = ", ".join(args[1:])
        else:
            args = ""
        return f"{var}.{fn.python_equivalent}({args})"

    def compile_generic_function_call(self, terminators=[], offset=False):
        """Compile fn([a [, b]]...)"""
        terminators.append(SymType.RIGHT_PAREN)
        func: SymFunction = self.current_token
        if func.ext_library:
            self.required_libraries[func.ext_library] = True
        args = self.parse_gather_function_args(terminators, True)
        joined_args = ",".join(args)
        if offset:
            return f"({func.python_equivalent}({joined_args})+{offset})"
        return f"{func.python_equivalent}({joined_args})"

    def compile_substr_function_call(self, terminators=[]):
        """Compile substr(str,start[,len])"""
        terminators.append(SymType.RIGHT_PAREN)
        func: SymFunction = self.current_token
        if func.ext_library:
            self.required_libraries[func.ext_library] = True
        args = self.parse_gather_function_args(terminators, True)
        string_name = args[0] if str(args[0]).isidentifier() else f"str({args[0]})"
        if len(args) == 2:
            if args[1].isnumeric():
                start = int(args[1]) - 1
                return f"({string_name}[{start}:])"
            start = args[1] if args[1].isnumeric() else f"int({args[1]})"
            return f"self._substr({string_name},{start})"
        if len(args) == 3:
            if args[1].isnumeric() and args[2].isnumeric():
                start = int(args[1]) - 1
                end = int(args[2]) + start
                return f"({string_name}[{start}:{end}])"
            start = args[1] if args[1].isnumeric() else f"int({args[1]})"
            length = args[2] if args[2].isnumeric() else f"int({args[2]})"
            return f"self._substr({string_name},{start},{length})"
        self.syntax_error("2 or 3 arguments")

    def compile_split_function_call(self, terminators=[]):
        """Compile split( str, array[, fieldsep])"""
        terminators.append(SymType.RIGHT_PAREN)
        position = self.prior_token.is_operator()
        func: SymFunction = self.current_token
        if func.ext_library:
            self.required_libraries[func.ext_library] = True
        args = self.parse_gather_function_args(terminators, True)
        # FIXME: args[0] self.fld
        string_name = args[0] if str(args[0]).isidentifier() else f"str({args[0]})"
        # split( str, array, fieldsep) -> array=str.split(fieldsep)
        if len(args) == 2:
            args.append("self.FS")
        if len(args) == 3:  # split( str, array, fieldsep) -> array=str.split(fieldsep)
            expr = f"{args[1]} = self._to_array({string_name}.split({args[2]}))"
            if position:
                tempvar = f"parts_{self.current_token_nr}"
                self.output_line(expr)
                self.output_line(f"{tempvar}=len(expr)")
                return tempvar
            else:
                return expr
        self.syntax_error("2 or 3 arguments")

    def compile_expression(self, extra_terminators=[]):
        """Assemble components until a terminator, usually ')' encountered"""
        terminators = [
            SymType.RIGHT_PAREN,
            SymType.LEFT_BRACE,
            SymType.RIGHT_BRACKET,
            SymType.END_OF_INPUT,
            SymType.STATEMENT_TERMINATOR,
        ]
        terminators.extend(extra_terminators)
        if self.current_token.is_operator():
            ans = self.compile_uni_operator()
        elif self.current_token.is_operand():
            if self.current_token.is_function():
                ans = [self.current_token.parser(terminators)]
            else:
                ans = [self.current_token.python_equivalent]
            self.advance_token()
        else:
            ans = []
        last_array = None
        last_ans_len = len(ans)
        while self.current_token.sym_type not in terminators:
            if self.prior_token.is_operand():
                if self.current_token.sym_type == SymType.AMBIGUOUSOPERATOR:
                    self.current_token = self.current_token.binary_op()
                if self.current_token.sym_type == SymType.LEFT_PAREN:
                    self.advance_token()
                    if self.current_token.sym_type == SymType.RIGHT_PAREN:
                        ans.append("()")  # empty argument list
                    else:
                        ans.append("(" + self.compile_expression() + ")")
                    self.advance_token()
                elif self.current_token.sym_type == SymType.LEFT_BRACKET:
                    # We need to save some current state in case we encounter ++ or --
                    # after the ]
                    last_array = self.prior_token
                    last_ans_len = len(ans)
                    # The same variable can't be both scalar & array in
                    # one program in AWK, so we just forcibly change the type
                    self.prior_token.is_array = True
                    self.prior_token.init = "defaultdict(AwkEmptyVar.instance)"
                    self.advance_token()
                    last_array_index = self.compile_expression()
                    self.advance_token()  # dispose ]
                    ans.append("[" + last_array_index + "]")
                elif self.current_token.token in ["++", "--"]:  # post_inc / post_dec
                    op = self.current_token.token
                    if self.prior_token.sym_type == SymType.VARIABLE:
                        var = self.prior_token
                        var_parts = var.python_equivalent.split(".", 1)
                        ans.pop()
                        op_fun = "_post_inc_var" if op == "++" else "_post_dec_var"
                        ans.append(f"{var_parts[0]}.{op_fun}('{var_parts[1]}')")
                    elif self.prior_token.token == "]":
                        # we have everything we need, just need to throw away
                        # earlier output and regenerate
                        op_fun = "_post_inc_arr" if op == "++" else "_post_dec_arr"
                        ans = ans[: last_ans_len - 1]
                        var_parts = last_array.python_equivalent.split(".", 1)
                        ans.append(
                            f"{var_parts[0]}.{op_fun}({last_array.python_equivalent},{last_array_index})"
                        )
                    self.advance_token()
                elif self.current_token.is_operator():
                    if self.current_token.token in ["~", "!~"]:
                        target = ans.pop()
                        test = self.current_token.token
                        ans.append(self.compile_regex(target, test))
                    else:
                        ans.append(self.current_token.python_equivalent)
                    self.advance_token()
                elif self.current_token.is_operand():
                    if self.current_token.sym_type == SymType.NUMBER:
                        # The lexer interprets -1 as the number -1 and not
                        # the two tokens - and 1. Quick fix:
                        ans.append("-")
                        ans.append(self.current_token.token[1:])
                    else:
                        # two operands together. String concatenation? Let's hope so
                        lhs = ans.pop()
                        while lhs[0] in ".[":  # rejoin array lookups
                            lhs = ans.pop() + lhs
                        if self.lookahead_token.sym_type == SymType.LEFT_BRACKET:
                            rhs = self.compile_expression(extra_terminators)
                        else:
                            rhs = self.current_token.python_equivalent
                        ans.append(f"(str({lhs})+str({rhs}))")
                    if not self.current_token.is_terminator():
                        self.advance_token()
                else:
                    self.syntax_error("operator")
            elif self.prior_token.is_operator():
                if self.current_token.is_operator():
                    self.compile_uni_operator(ans)
                elif self.current_token.is_function():
                    ans.append(self.current_token.parser())
                elif self.current_token.is_operand():
                    ans.append(self.current_token.python_equivalent)
                else:
                    self.syntax_error("operator or operand")
                if not self.current_token.is_terminator():
                    self.advance_token()
            else:
                self.syntax_error("operator or operand2")
        return "".join(ans)

    def compile_condition(self, terminator, consume_terminator=False):
        ans = self.compile_expression()
        if consume_terminator:
            self.advance_token()
        return ans

    """Statements and blocks"""

    def compile_exit_statement(self):
        """
        exit [code]
        """
        self.advance_token()
        if self.current_token.sym_type == SymType.STATEMENT_TERMINATOR:
            expr = "0"
        else:
            expr = self.compile_expression()
        self.output_line("AwkpyRuntimeWrapper._ans=" + expr)
        self.output_line("raise AwkExit")
        if self.current_token.sym_type == SymType.STATEMENT_TERMINATOR:
            self.consume_terminator()

    def compile_simple_command(self):
        """
        Commands that require neither logic
        nor non-trivial translation:
            break, continue
        """
        self.output_line(self.current_token.python_equivalent)
        self.advance_token()
        if self.current_token.sym_type == SymType.STATEMENT_TERMINATOR:
            self.consume_terminator()

    def compile_expression_command(self):
        """
        Commands that require an optional expression:
            return
        """
        command = self.current_token.python_equivalent
        self.advance_token()
        if self.current_token.sym_type == SymType.STATEMENT_TERMINATOR:
            expr = ""
        else:
            expr = " " + self.compile_expression()
        self.output_line(command + expr)
        if self.current_token.sym_type == SymType.STATEMENT_TERMINATOR:
            self.consume_terminator()

    def compile_function_def(self):
        """
        definition of function( args ) statement
        """
        former_output_section = self.current_output
        self.current_output = self.function_section
        self.advance_token()  # discard function
        func_sym = SymFunction(self.current_token.token, user_defined=True)
        func_name = func_sym.python_equivalent[5:]  # remove the self. from the def
        function_line = "def " + func_name + "(self"
        self.syms[func_sym.token] = func_sym
        self.replacement_syms[func_sym.token] = func_sym
        self.current_token = func_sym
        self.advance_token()  # discard function name
        self.advance_token()  # discard (
        parameter_dict = {}
        parameter_list = []
        # process parameters. Note that parameters are local & not member variables
        while self.current_token.sym_type == SymType.VARIABLE:
            param = self.current_token
            parameter_dict[param.token] = (
                param,
                param.python_equivalent,
            )  # save for restore
            param.python_equivalent = param.token
            parameter_list.append(f"{param.token}=AwkEmptyVarInstance")
            self.advance_token()  # discard parameter name
            if self.current_token.sym_type == SymType.COMMA:
                self.advance_token()  # discard ,
        self.advance_token()  # discard )
        if self.current_token.sym_type == SymType.STATEMENT_TERMINATOR:
            self.consume_terminator()
        if len(parameter_list) == 0:
            function_line += "):"
        else:
            function_line += ", " + ", ".join(parameter_list) + "):"
        saved_indent = self.indent
        self.indent = self.indent[4:]
        self.output_line(function_line)
        self.indent = saved_indent
        if len(parameter_list) > 0:
            self.output_line("_locals=AwkpyRuntimeVarOwner()")
            for varname, data in parameter_dict.items():
                var, value = data
                self.output_line(
                    f"_locals.{var.python_equivalent}={var.python_equivalent}"
                )
                var.python_equivalent = f"_locals.{var.python_equivalent}"
        self.compile_statement()
        self.indent = saved_indent
        for varname, data in parameter_dict.items():
            var, value = data
            var.python_equivalent = value
        self.current_output = former_output_section
        if self.current_token.sym_type == SymType.STATEMENT_TERMINATOR:
            self.consume_terminator()

    def compile_if_statement(self):
        self.advance_token_require(sym_types=[SymType.LEFT_PAREN])  # discard "if"
        self.advance_token()
        condition = self.compile_expression()  # (')',True)
        self.output_line(f"if {condition}:")
        if self.current_token.token == ")":
            self.advance_token()
        self.compile_indented_statement()
        if self.current_token.token == "else":
            self.output_line("else:")
            self.advance_token()
            if self.current_token.token == "\n":
                self.consume_terminator()
            self.compile_indented_statement()

    def compile_while_statement(self):
        self.advance_token_require(sym_types=[SymType.LEFT_PAREN])  # discard "while"
        self.advance_token()
        condition = self.compile_condition(")", True)
        self.output_line(f"while {condition}:")
        self.compile_indented_statement()

    def compile_do_statement(self):
        """
        AWK has a C style do statement, Python does not, so
        we turn do into a while statement.
        To translate, we need to move the condition from the
        bottom of the loop to the top and modify it.
        Some juggling is required.
        """
        self.advance_token()  # discard "do"
        saved_output = self.start_defer_output()
        self.compile_indented_statement()
        if self.current_token.token != "while":
            self.syntax_error("'while'")
        self.advance_token()
        do_body_output = self.end_deferred_output(saved_output)
        if self.current_token.token != "(":
            self.syntax_error("'('")
        self.advance_token()
        condition = self.compile_condition(")", True)
        if (
            self.current_token.sym_type == SymType.STATEMENT_TERMINATOR
            and self.current_token.consume
        ):
            self.consume_terminator()
        first_time = f"do_first_{self.current_token_nr}"
        condition = f"{first_time} or ({condition})"
        self.output_line(f"{first_time}=True")
        self.output_line(f"while {condition}:")
        self.output_line(f"    {first_time}=False")
        self.output_block(do_body_output)

    def compile_for_statement(self):
        """AWK has two types of for statements, C style and
        something similar to python's
        for( initialise;condition;incr)
        for( var in array )
        first step is to work out what we are dealing with
        """
        self.advance_token_require(sym_types=[SymType.LEFT_PAREN])
        self.advance_token()
        if (
            self.current_token.sym_type == SymType.VARIABLE
            and self.lookahead_token.token == "in"
        ):
            # python style
            var: SymVariable = self.current_token
            self.advance_token()
            self.advance_token_require(sym_types=[SymType.VARIABLE])
            arr: SymVariable = self.current_token
            arr.init = "defaultdict(AwkEmptyVar.instance)"
            arr.is_array = True
            self.output_line(f"for {var.python_equivalent} in {arr.python_equivalent}:")
            self.advance_token()  # dispose of )
            self.advance_token()
            self.compile_indented_statement()
        else:
            """C style
                for( init; test; incr) body
            ->
                def _generator__token_nr(): # self & locals avail
                    init
                    while test:
                        yield True
                        incr
                for dummy in self._generator__token_nr([locals])
                    body
            # this structure allows for continue statements
            """
            init = self.compile_expression()
            self.advance_token()  # dispose of ;
            test = self.compile_expression()
            self.advance_token()  # dispose of ;
            if self.current_token.sym_type != SymType.RIGHT_PAREN:
                ## For unknown reasons incr gets doubled up under pytest
                ## can not reproduce this otherwise
                o1 = self.current_token
                o2 = self.lookahead_token
                incr = self.compile_expression()
                if "')self" in incr:
                    if o1.token[0] in "+-":
                        incr = f"{o2.python_equivalent} {o1.token[0]}=1"
                    else:
                        incr = f"{o1.python_equivalent} {o2.token[0]}=1"
            else:
                incr = ""
            if self.current_token.sym_type == SymType.RIGHT_PAREN:
                self.advance_token()  # dispose of )
            # former_output_section = self.current_output
            # self.current_output=self.function_section
            generator_name = f"_generator__{self.current_token_nr}"
            dummy_name = f"_dummy__{self.current_token_nr}"
            self.output_line(f"def {generator_name}():")
            if init.strip() != "":
                self.output_line(f"    {init}")
            if test.strip() == "":
                test = "True"
            self.output_line(f"    while {test}:")
            self.output_line(f"        yield True")
            if incr.strip() != "":
                self.output_line(f"        {incr} #")
            self.output_line(f"for {dummy_name} in {generator_name}():")
            self.compile_indented_statement()

    def compile_print_statement(self):
        self.advance_token()  # discard "print"
        ans = "print(f'"
        while self.current_token.sym_type != SymType.STATEMENT_TERMINATOR:
            if self.current_token.sym_type == SymType.STRING:
                text = self.current_token.python_equivalent[1:-1]
                ans += text
            elif (
                self.current_token.is_variable()
                and self.current_token.is_array
                and self.lookahead_token.sym_type == SymType.LEFT_BRACKET
            ):
                var = self.current_token.python_equivalent
                self.advance_token()
                self.advance_token()
                index = self.compile_expression()
                ans += "{" + var + ".get(" + index + ',"")}'
            elif self.current_token.sym_type in [SymType.VARIABLE, SymType.DOLLAR]:
                ans += "{" + self.current_token.python_equivalent + "}"
            elif self.current_token.sym_type == SymType.COMMA:
                ans += "{self.OFS}"
            else:
                ans += f"{self.current_token.python_equivalent}"
            self.advance_token()
        self.consume_terminator()
        if ans == "print(f'":  # print; == print $0;
            ans += "{self._FLDS[0]}"
        ans += "')"
        self.output_line(ans)

    def compile_block(self):
        """consume { statement; ... }"""
        if self.current_token.sym_type != SymType.LEFT_BRACE:
            self.syntax_error("'{'")
        self.advance_token()
        while self.current_token.token != "}":
            self.compile_statement()
        self.advance_token()

    def compile_statement(self):
        """consume a simple statement or a block"""
        if self.current_token.token == "\n":
            self.advance_token()
        prog = None
        if self.current_token.sym_type == SymType.STATEMENT:
            self.current_token.parse()
        elif self.current_token.sym_type == SymType.LEFT_BRACE:
            self.compile_block()
        elif self.current_token.sym_type in [
            SymType.LEFT_PAREN,
            SymType.VARIABLE,
            SymType.FUNCTION,
            SymType.AMBIGUOUSOPERATOR,
            SymType.UNIOPERATOR,
        ]:
            prog = self.compile_expression()
        elif self.current_token.token != "}":
            self.syntax_error("a statement")
        if (
            self.current_token.sym_type == SymType.STATEMENT_TERMINATOR
            and self.current_token.consume
        ):
            self.advance_token()
        if prog:
            self.output_line(prog)

    def compile_indented_statement(self):
        """Indent the output then compile"""
        saved_indent = self.indent
        self.indent += "    "
        self.compile_statement()
        self.indent = saved_indent

    def compile_pattern_condition(self):
        """consume [condition] { statement; ... }"""
        prog = None
        while self.current_token.token == "\n":
            self.advance_token()
        if self.current_token.sym_type == SymType.END_OF_INPUT:
            return
        if self.current_token.sym_type == SymType.SECTION:
            former_output_section = self.current_output
            self.current_output = self.current_token.awk_priority
            self.advance_token()
            self.compile_block()
            self.current_output = former_output_section
        elif self.current_token.sym_type == SymType.LEFT_BRACE:
            self._has_mainloop = True
            self.compile_block()
        elif self.current_token.token == "function":
            self.compile_function_def()
        else:  # some type of condition
            self._has_mainloop = True
            if self.current_token.sym_type == SymType.LEFT_PAREN:
                prog = self.compile_expression()
            elif self.current_token.sym_type in [
                SymType.FUNCTION,
                SymType.VARIABLE,
                SymType.DOLLAR,
                SymType.NUMBER,
                SymType.LEFT_PAREN,
            ]:
                prog = self.compile_condition("{")
            elif self.current_token.token == "/" or self.current_token.is_regex():
                self.output_line("if " + self.compile_regex("self._FLDS[0]", "~") + ":")
                if self.current_token.is_regex() or self.current_token.token == "/":
                    self.advance_token()
                self.compile_indented_statement()
            else:
                self.syntax_error("a condition")
        if prog:
            self.output_line("if " + prog + ":")
            self.compile_indented_statement()

    def compile_to_segments(self, source):
        if len(source) > 2 and source[0:2] == "-f":
            filename = source[2:]
            if filename in self.included_files:
                raise SyntaxError(
                    f"{filename} can't be used as both included and as a source file "
                )
            self.source_files.append(filename)
            file = open(filename, mode="r")
            source = file.read()
            file.close()
        elif len(source) > 2 and source[0:2] == "-i":
            filename = source[2:]
            if filename in self.source_files:
                raise SyntaxError(
                    f"{filename} can't be used as both included and as a source file "
                )
            if filename in self.included_files:
                return
            self.included_files.append(filename)
            file = open(filename, mode="r")
            source = file.read()
            file.close()
        elif len(source) > 2 and source[0:2] == "-e":
            filename = "command line"
            source = source[2:]
        else:
            filename = "command line"
        self.tokens = self.lex_string(filename, source + "\n")
        self.current_token_nr = -2
        self.advance_token()
        self.advance_token()
        self.indent = "        "
        while (
            self.current_token_nr < len(self.tokens)
            and self.current_token.sym_type != SymType.END_OF_INPUT
        ):
            self.compile_pattern_condition()
        return self.generated_code

    def parse_args(self, source):
        files = []
        # Experiments show Gawk excludes options from ARGC & ARGV
        i = 0
        while i < len(source):
            arg = source[i]
            if arg[0] == "-":
                if arg[1] == "-":
                    if len(arg) > 2:  # gnu style arg
                        print(f"{arg}: Gnu style arguments not implemented")
                        exit(1)
                    else:  # end of options, ignore everything
                        i += 1
                        return files
                if arg[1] == "i":
                    if len(arg) == 2:
                        i += 1
                        files.append("-i" + source[i])
                    else:
                        files.append(arg)
                if arg[1] == "f":
                    if len(arg) == 2:
                        i += 1
                        files.append("-f" + source[i])
                    else:
                        files.append(arg)
                elif arg[1] == "e":
                    if len(arg) > 2:
                        files.append(arg[2:])
                    else:
                        i += 1
                        files.append(source[i])
                elif arg[1] == "v":
                    # gawk documentations suggests a space is required after the
                    # v, but it & every other awk I've used has the space optional
                    if len(arg) > 2:
                        optn = arg[2:].split("=", 1)
                    else:
                        i += 1
                        optn = source[i].split("=", 1)
                    setvar = optn[0]
                    val = optn[1]
                    # gawk accepts -v namespace::name=whatever.
                    # now we have namespaces these should be supported
                    if "::" in setvar:
                        optn = setvar.split("::", 1)
                        namespace_name = optn[0]
                        setvar = optn[1]
                        namespace = AwkNamespace.get_namespace(namespace_name)
                    else:
                        namespace = AwkNamespace.awk_awk_namespace
                    setvar_key = namespace.decorated + setvar
                    sym = self.syms.get(setvar_key, None)
                    if sym is None:
                        sym = SymVariable(
                            setvar_key,
                            python_equivalent=namespace.python_equivalent + setvar,
                        )
                        self.syms[setvar_key] = sym
                    # HEURISTIC: if the value is a number, leave it and let Python
                    # convert it to one
                    # If the value is not a number, surround with quotes.
                    # Damned if I know if this is the correct thing to do
                    # it duplicates what we do in the runtime so if we change
                    # one we should change both.
                    try:
                        discard = float(val)
                    except:
                        val = 'r"""' + val + '"""'
                    sym.init = val
            else:
                files.append(arg)
            i += 1
        if i < len(source):
            print(f"internal error, not all options consumed")

        return files

    def import_library(self, library):
        if self.imported_libraries.get(library) is None:
            if self.compile_to_disk:
                ans = f"import {library}"
            else:
                ans = f'{library}=__import__("{library}")'
            self.imported_libraries[library] = True
        else:
            ans = f"# Compiler oopsie? Dup import of {library}"
        return ans

    def import_from_library(self, library, items):
        if self.compile_to_disk:
            ans = [f"from {library} import " + ", ".join(items)]
        else:
            if self.imported_libraries.get(library) is None:
                ans = [self.import_library(library)]
            else:
                ans = []
            for item in items:
                ans.append(f"{item}={library}.{item}")
        return ans

    def compile(self, args):
        if isinstance(args, list):
            files = self.parse_args(args)
            for s in files:
                self.compile_to_segments(s)
        else:
            self.compile_to_segments(args)

        self.current_output = 0  # __init__
        self.output_line("super().__init__()")
        if self._has_mainloop:
            self.output_line("self._has_mainloop = True")

        for name, sym in self.syms.items():
            if sym.is_variable():
                if sym.is_array and sym.is_scalar:
                    raise SyntaxError(
                        f"{sym.token} is used as both an array and a scalar value"
                    )
                if not sym.is_built_in():
                    self.output_line(f"{sym.python_equivalent}={sym.init}")

        if self.do_debug:
            print([t.token for l, t in self.tokens])
        self.required_library_items["collections"]["defaultdict"] = True
        prefix = ["#! /usr/bin/python3"]
        for (
            item
        ) in "AwkpyRuntimeVarOwner,AwkpyRuntimeWrapper,AwkNext,AwkNextFile,AwkExit,AwkEmptyVar,AwkEmptyVarInstance".split(
            ","
        ):
            self.required_library_items["awkpy_runtime"][item] = True
        prefix.append(self.import_library("re"))
        prefix.append(self.import_library("sys"))
        for ext_lib in self.required_libraries:
            prefix.append(self.import_library(ext_lib))
        for ext_lib, items in self.required_library_items.items():
            prefix.extend(self.import_from_library(ext_lib, items))
        prefix.extend(
            [
                "class AwkPyTranslated(AwkpyRuntimeWrapper):",
                "    global AwkEmptyVarInstance",
            ]
        )
        prog = "\n".join(prefix)
        # functions have a jagged indenting less than regular sections
        if len(self.generated_code[self.function_section]) > 0:
            prog += "\n" + "\n".join(self.generated_code[self.function_section])
        fns = [
            "__init__(self)",
            "BEGIN",
            "BEGINFILE",
            "MAINLOOP",
            "ENDFILE",
            "END",
        ]
        for outputNr in range(6):
            if len(self.generated_code[outputNr]) > 0:
                fn = fns[outputNr]
                if "(self" not in fn:
                    fn += "(self)"
                prog += f"\n    def {fn}:\n" + "\n".join(self.generated_code[outputNr])
        if self.do_debug:
            print(prog)
        return prog

    def __init__(self, compile_to_disk=False, debug=False):
        self.do_debug = debug
        self.compile_to_disk = compile_to_disk
        self.generated_code = [
            [],
            [],
            [],
            [],
            [],
            [],
            [],
        ]  # __init__, BEGIN, BEGINFILE, MAINLOOP, ENDFILE, END, functions
        self.current_output = 3  # body
        self._has_mainloop = False
        """regular expression that should recognise all awk symbols"""
        comment = r"#.*$"
        string = r'"(([^\\](\\\\)*\\")|([^"\n]))*("|$)'
        # Not strictly correct, but we just treat character constants the same as strings
        # and leave it for later stages to sort it out.
        chars = string.replace('"', "'")
        regexs = r"(^|(!~)|([~(,]))\s*/((\[[^\]]*\])|([^/\n]))*(/|$)"
        ident = r"(@?|\$+)[A-Za-z_][A-Za-z_0-9]*(::[A-Za-z_][A-Za-z_0-9]*)?"
        dollar = r"[$]+([0-9]*)"  # only $ number as $ident already recognised by ident
        num = r"(0x?)?[-]?[0-9]+(\.[0-9]+)?"
        ops = r"(!~)|(\+\+)|(--)|(\*\*)|(\|\|)|(&&)|(!~)|(<<)|(>>)|([-+*/%^=!<>]=)|([-+*/%^!~(){},.:;[\]$])"
        pattern = rf"({comment})|({string})|({chars})|({regexs})|({ident})|({dollar})|({num})|({ops})"
        self.lexre = re.compile(pattern)
        self.lexre_octal = re.compile(r"0[0-7]+")  # octal integers
        self.lineNr = 0
        self.indent = "        "
        global default_function_parser
        default_function_parser = lambda t=[]: self.compile_generic_function_call(t)
        global default_function_method_parser
        default_function_method_parser = (
            lambda t=[]: self.compile_function_call_to_method(t)
        )
        self.source_files = []
        self.included_files = []
        self.imported_libraries = {}
        self.required_libraries = {}
        self.required_library_items = defaultdict(dict)  # dict of dicts
        # AWK string functions are 1 based, Python 0 based.
        offset_function_parser = lambda t=[]: self.compile_generic_function_call(
            t, offset=1
        )
        self.syms = {}
        for sym in [
            # various brackets
            Sym("{", SymType.LEFT_BRACE, 1, 1),
            Sym("[", SymType.LEFT_BRACKET, 1, 1),
            Sym("]", SymType.RIGHT_BRACKET, 1, 1),
            Sym("(", SymType.LEFT_PAREN, 1, 1),
            Sym(")", SymType.RIGHT_PAREN, 1, 1),
            # Field reference
            Sym("$", SymType.DOLLAR, 2, -1),
            # unary operators
            Sym("--", SymType.UNIOPERATOR, 3, -1),
            Sym("++", SymType.UNIOPERATOR, 3, -1),
            Sym("**", SymType.UNIOPERATOR, 4, 4),
            Sym("^", SymType.UNIOPERATOR, 4, 4, python_equivalent="**"),  # alias for **
            Sym("!", SymType.UNIOPERATOR, 5, 14, "not"),
            Sym("*", SymType.BINOPERATOR, 6, 6),
            Sym("%", SymType.BINOPERATOR, 6, 6),
            Sym("/", SymType.BINOPERATOR, 6, 6),
            SymAmbiguous(
                Sym("-", SymType.UNIOPERATOR, 5, 5), Sym("-", SymType.BINOPERATOR, 7, 7)
            ),
            SymAmbiguous(
                Sym("+", SymType.UNIOPERATOR, 5, 5), Sym("+", SymType.BINOPERATOR, 7, 7)
            ),
            #   Sym('', SymType.BINOPERATOR, 8, 5, python_equivalent='+'), # Awk just concatenates, no operator
            Sym("<", SymType.BINOPERATOR, 9, 14),
            Sym("<=", SymType.BINOPERATOR, 9, 14),
            Sym("==", SymType.BINOPERATOR, 9, 14),
            Sym("!=", SymType.BINOPERATOR, 9, 14),
            Sym(">", SymType.BINOPERATOR, 9, 14),
            Sym(">=", SymType.BINOPERATOR, 9, 14),
            Sym("|", SymType.BINOPERATOR, 9, 9),
            Sym("&", SymType.BINOPERATOR, 9, 9),
            Sym("|&", SymType.BINOPERATOR, 9, 9),
            #   Sym('>>', SymType.BINOPERATOR, 9, ), I/O
            SymAmbiguous(
                Sym("~", SymType.UNIOPERATOR, 5, 5),
                Sym("~", SymType.BINOPERATOR, 15, 15),
            ),
            SymAmbiguous(
                Sym("!~", SymType.UNIOPERATOR, 5, 5),
                Sym("!~", SymType.BINOPERATOR, 15, 15),
            ),
            Sym(
                "in", SymType.BINOPERATOR, 16, 16
            ),  # ??? is this the same in both languages
            Sym("+=", SymType.BINOPERATOR, 20, 20),
            Sym("-=", SymType.BINOPERATOR, 20, 20),
            Sym("*=", SymType.BINOPERATOR, 20, 20),
            Sym("/=", SymType.BINOPERATOR, 20, 20),
            Sym("%=", SymType.BINOPERATOR, 20, 20),
            Sym(".", -1, 20, 20),  # FIXME, where does this come from?
            Sym("=", SymType.BINOPERATOR, 20, 20),  # not an operator in Python. c.v. :=
            #
            #   Built-in variables
            #
            SymVariable("ARGC", built_in=True, scalar=True),
            SymVariable("ARGV", built_in=True, array=True),
            SymVariable("FILENAME", built_in=True, scalar=True),
            SymVariable("FNR", built_in=True, scalar=True),
            SymVariable("FS", built_in=True, scalar=True),
            SymVariable("NF", built_in=True, scalar=True),
            SymVariable("NR", built_in=True, scalar=True),
            SymVariable("OFS", built_in=True, scalar=True),
            SymVariable("ENVIRON", built_in=True, array=True),
            # To implement ARGIND, CONVFMT, ERRNO, FUNCTAB, OFMT, ORS, RLENGTH, RS, RSTART, SUBSEP,SYMTAB
            # functions = ??
            # __init__ = ??
            Sym("EndOfInput", SymType.END_OF_INPUT),
        ]:
            self.syms[sym.token] = sym
        #
        # Reserved words. Add to self.syms & self.reserved_words
        #
        self.reserved_words = {}
        for sym in [
            #
            #   functions
            #
            SymFunction("atan2", python_equivalent="math.atan2"),
            SymFunction("cos", python_equivalent="math.cos"),
            SymFunction("exp", python_equivalent="math.exp"),
            SymFunction("int", python_equivalent="int"),
            SymFunction("length", python_equivalent="len"),
            SymFunction("log", python_equivalent="math.log"),
            SymFunction("rand", python_equivalent="random.random"),
            SymFunction("srand", python_equivalent="random.seed"),
            SymFunction("sin", python_equivalent="math.sin"),
            SymFunction("split", lambda t=[]: self.compile_split_function_call(t)),
            SymFunction("sqrt", python_equivalent="math.sqrt"),
            SymFunction("substr", lambda: self.compile_substr_function_call()),
            SymFunction("tolower", default_function_method_parser, "lower"),
            SymFunction("toupper", default_function_method_parser, "upper"),
            #
            #   Unimplemented functions
            #
            Sym("close", SymType.RESERVED_WORD),
            Sym("gsub", SymType.RESERVED_WORD),
            Sym("index", SymType.RESERVED_WORD),
            Sym("match", SymType.RESERVED_WORD),
            Sym("sprintf", SymType.RESERVED_WORD),
            Sym("sub", SymType.RESERVED_WORD),
            Sym("system", SymType.RESERVED_WORD),
            #
            #   Statements
            #
            SymStatement("break", lambda: self.compile_simple_command()),
            SymStatement("continue", lambda: self.compile_simple_command()),
            SymStatement("do", lambda: self.compile_do_statement()),
            SymStatement("exit", lambda: self.compile_exit_statement()),
            SymStatement("for", lambda: self.compile_for_statement()),
            SymStatement("function", lambda: self.compile_function_def()),
            SymStatement("if", lambda: self.compile_if_statement()),
            Sym("else", SymType.RESERVED_WORD),
            SymStatement(
                "next",
                lambda: self.compile_simple_command(),
                python_equivalent="raise AwkNext",
            ),
            SymStatement(
                "nextfile",
                lambda: self.compile_simple_command(),
                python_equivalent="raise AwkNextFile",
            ),
            SymStatement("print", lambda: self.compile_print_statement()),
            SymStatement("return", lambda: self.compile_expression_command()),
            SymStatement("while", lambda: self.compile_while_statement()),
            SymTerminator(";", True, False, "\n"),
            SymTerminator("\n", True, True),
            SymTerminator("}", False, False),
            #
            #   Unimplemented statements
            #
            Sym("delete", SymType.RESERVED_WORD),
            Sym("getline", SymType.RESERVED_WORD),
            Sym("in", SymType.RESERVED_WORD),
            Sym("printf", SymType.RESERVED_WORD),
            #
            #   Non operators
            #
            Sym("BEGIN", SymType.SECTION, 1),
            Sym("BEGINFILE", SymType.SECTION, 2),
            # body = 3
            Sym("ENDFILE", SymType.SECTION, 4),
            Sym("END", SymType.SECTION, 5),
        ]:
            self.syms[sym.token] = sym
            self.reserved_words[sym.token] = sym
        self.replacement_syms = {}
        self.current_token: Sym = self.syms["+"]  # dummy
        self.current_line = -1
        self.prior_token: Sym = self.current_token
        self.lookahead_line = -1
        self.lookahead_token: Sym = self.current_token
        self.function_section = 6  # ("END")+1
        self.current_token_nr = -1


if __name__ == "__main__":
    source = r"""BEGIN {
    x="123./456..789.101112"
    split(x,y,"./")
    exit y[1]
    }"""
    source = r"""BEGIN {
    a="<>"
    b = a a
    print b
    }"""
    source = r"""BEGIN {
    a[1]="<>"
    print a[1] a[1]
    }"""
    source = r"""BEGIN {
    a[1]="<>"
    b = a[1] a[1]
    print b
    }"""
    source = r"""END {
    OFS="-"
    l="left";
    r="right";
    print l,r
    }"""
    source = r"""BEGIN {
    i=0;
    t=6;
    while(t>1) {
        t-=1;
        i+=1;
    }
    print t":"i
}"""
    source = r"""BEGIN {
    var="start"
    astr=substr("string",3,1)
    if( var~astr ) exit 1
    exit 0
}"""
    source = r"""@include "tests/add_1_in_BEGIN.awk"
    @include "tests/add_1_in_BEGIN.awk"
    BEGIN {
    exit a
}"""
    a = AwkPyCompiler()
    code = a.compile(source)
    print(code)
