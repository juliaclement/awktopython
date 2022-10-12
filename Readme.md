# AWK To Python Translator

## Purpose

awktopy is designed to convert a large subset of the AWK language into
Python 3.8 and later. It is being developed & tested under Cpython
3.10.7 & pypy-7.3.9 which documents that it has Python 3.8
compatibility,

The translated program can either be immediately executed or saved for
later execution.

## Usage

### Compile to a Python File

python awkpycc.py \[options\] \[awk-program\]

#### options:

\-o filename Save the generated python to filename. Default is the first .awk source file with the extension changed to py

\-d Turn on some (not often very useful) debugging information on internal compiler data

\-e awk-program-string Awk source code. Normally when awk code is on the command line, it is the only awk source. -e allows awk code in files and on the command line to be merged into a single Python program. This option may be used multiple times.

\-f awk-program-file The name of the Awk source code. This option may be used multiple times.

\-F string.	Set the FS (field separator) variable. Implemented by translating into -vFS=string.

\-i awk-include-file The name of an Awk source code file. This is a Gawk extension that is very similar to -f but only includes the file once. Will error if the same file is (both -f and -i) included through both.

\-v variable=value Assign value as the initial value of the named variable before the program, including the BEGIN block if any, is executed.

Once namespaces are implemented, the variable name may be prefixed with namespace:: to assign variables in a specific namespace. For now, only the default awk: namespace is available, it is discarded.

\--Stop processing options & treat the rest of the command line as runtime filenames. These are ignored in compile mode, see Compile &
Execute. They are not passed through to the generated Python.

\-Wprofile (also -Wcprofile). Compile a call to cProfile into the generated code.

\-Wr Stop processing options & treat the rest of the command line as runtime options and filenames. These are ignored in compile mode, see Compile & Execute. They are not passed through to the generated Python.
This is an awkpy extension.

Awk-program A quoted string containing the code of the awk program to be compiled. If you prefix it with -e, you can have multiple strings and mix them with awk files.

## Compile & Execute

python awkpy.py \[options\] \[awk-program\] \[input-files and variable-settings\]

The options are the same as for awkpycc.py above, except as noted:

### options:

\-o filename Save the generated python to filename. Default is not to save the Python code to disk. If you do save the Python, please be aware that using pythons compile() and exec() methods have forced us to make some minor changes when compared to awkpycc generated code. They should be functionally identical.

\-- Stop processing options & treat the rest of the command line as input files to the generated program. This can be useful if you have a data file to be process that has a name starting in a hyphen

\-Wr Stop processing options & treat the rest of the command line as runtime options and filenames, these are excuted inside the generated code. This is an awkpy extension. 

Input - filesData to be fed to the compiled program. Files are processed left to right. If no files are specified, stdin is used. If you want to input both files and stdin, you can represent this by using the magic filename – where you want stdin to be in the list of files.

Variable-settings This allows a variable in the running AWK program to be set. It is very similar to the -v option except the assignment happens after the preceding file has been fully processed and before the following file is opened. The syntax is name=value.

### Executing compiled programs

python name.py \[options\] \[input-files and variable-settings\], or if name.py is in the current path, it is tagged as executable so name.py \[options\] \[input-files and variable-settings\] can be used.

All the options available in Compile or Compile & Execute are recognised, but only -v, --, -, and -d are likely to do anything.

## Source

### Language

There are a number of implementations & thus possibly dialects of AWK:
nawk (aka “BWK awk, “one true AWK”), mawk, Jawk, BusyBox AWK, CLAWK and GAWK to name a few. POSIX has standardised the language
https://pubs.opengroup.org/onlinepubs/9699919799/utilities/awk.html
but this is a bit hard to follow in places so I have used the GAWK manual as my primary source document, but where they note that a feature
is a GAWK extension I make a value judgement on supporting it. For example:
* GAWK has BEGINFILE and ENDFILE special patterns as extensions. They     were trivial to implement, so I did.
* GAWK has a C style switch statement as an extension. Python lacks this construct and implementation looks hard so I arbitrarily decided not to implement it.

That aside, I am treating POSIX compatibility as a major design goal.

### Implementation limits

awktopy is being developed in an incremental manner. The full source
language is not yet, and may never be, implemented. See the
Implementation\_State document in the docs folder for the current status
of the implementation.

#### Correctness (of AWK program)

Unlike most language translators, pytoawk assumes that its input is a correct, preferably debugged, awk program. This means it tries to recognise well formed AWK and does not try very hard to detect invalid cases. This may cause strange crashes when the generated code is run.
The moral of the story is to test your awk source in an awk interpreter before feeding it into awktopy.

As examples:
- awk does not permit the same variable to be used as both a scalar value and an array. We don’t check for this. Any attempt to mix types like this will probably result in a crash.
- Awk does not permit a function name (built-in or user defined) to be used as a parameter name in a built-in function. I have plans for partially implementing this check but fully checking for it would require a degree of look-ahead in the compiler which I am loathe to implement.


