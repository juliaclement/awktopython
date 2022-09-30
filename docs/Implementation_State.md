# Awktopy Implementation Status

## Notes

Each item is presented as name (source) status where source is one of nawk, POSIX, GAWK to indicate where I know it from; status will be one of “implemented”, “planned” or “rejected”

## Compile Time

Program on command line (nawk) Implemented

awk accepts a command line like awk ‘an awk program’ ... datafiles

Multiple Source Files (nawk) implemented

awk accepts a command line like “awk -f “prog1.awk” -f “prog2” ... datafiles
the files are compiled in order and then produce a single execution
unit.

Gawk has a “-i” option which is like “-f” but will only include any given file once. Will produce an error message if the same file is included through both -i & -f.

@include (gawk extension) implemented since rewrite of tokenizer.

@namespace (gawk extension) implemented.

@import (possible awkpy extension) Gawk allows extensions written in the C language. Python also has this ability, I’m thinking a general ability to import Python modules or libraries could be useful in its own right, the Python extension would then be free to import C libraries using the appropriate cpython or pypy mechanisms. Would require some changes to
the lexer & symbol table.

### Patterns

- **BEGIN, END** (nawk): Fully implemented

- **BEGINFILE, ENDFILE** (GAWK): Fully implemented

- /pattern/ {statements} (nawk): fully implemented(\*)

- condition (e.g. $2==”x”) {statements} (nawk): fully implemented

- **function**(args) (nawk): Fully implemented except:

- Restrict arg names to not the same as a function name: planned, low priority

- nawk & gawk but not POSIX allow “func” as an alias of “function”. It would be a 1 line change in the parser, but the POSIX standard includes this text “This has been deprecated by the authors of the language, who asked that it not be specified.” so I probably won’t

**The POSIX standard says**

“Either the pattern or the action (including the enclosing brace characters) can be omitted.

A missing pattern shall match any record of input, and a missing action shall be equivalent to: { print }”

Omitted patterns are fully implemented. Omitted action is planned, but medium to low priority.

### Statements

simple statement: (expression;) (nawk) fully implemented

block statement: ({ statement;statement;...}) (nawk) fully implemented

**delete**: implemented both whole array and single element.

**if** (condition) statement \[else statement\] (nawk) fully implemented

**while** (condition) statement (nawk) fully implemented

**do** statement **while** (condition) (nawk) fully implemented

**for**(initialiser, condition, incr) statement (nawk) fully implemented

**print** (to stdout) (nawk) implemented, may not have all edge cases implemented.

**printf** (to stdout) (nawk) implemented as a simple wrapper around sprintf, may not have all edge cases implemented.

other I/O not implemented yet. Priority of each case needs to be determined.

### Expressions

Most unary & binary operators are recognised and passed straight through
to Python, even though in a couple of cases the priority of the operators is different in the two languages.

\++,-- are recognised & implemented through subroutines

Indirect function calls (Gawk extension) not yet implemented but look interesting.

Gawk optionally includes arbitrary-precision math libraries. Python ones such as mpmath or the standard decimal are available. Check to see how much work would be required to interface one.

### Lexer

As the first stage of compilation, the source programs are broken up into a series of tokens (names, strings, operators, etc.) by a routine known as the lexer. This has recently been replaced by a better one.

### Conditions

Currently these are treated as expressions and then fed to Python. I’m sure edge cases will eventually be found

## Runtime

Multiple data files (nawk) fully implemented

input from stdin (nawk) fully implemented

NB: POSIX spec says “The standard input shall be used only if no file operands are specified, or if a file operand is '-', or if a progfile
option-argument is '-'” The first two parts of this are implemented, the option-argument is planned, priority medium

\-v var=value (nawk) implemented for scalars. Need to research how it
affects arrays

var=value variable-assignment arguments (since early awk) implemented. 

\-F x, implemented by translating to -v FS=x

### Environment Variables

**ENVIRON** Read implemented by copying to a local dict during start-up. No reverse copy provided, required before creating the ability to execute external programs, medium priority.

### Built-in Functions

#### POSIX

Implemented: atan2, cos, exp, gsub, int, length, rand, sprintf, srand, sin, split, sub, substr, sqrt, tolower, toupper

Not Implemented: close, index, log, match, system. All high priority.

#### GAWK extensions

systime(), strftime(format, timestamp) unimplemented, medium priority.
Should be easy as python & AWK have very similar functions; in both cases, the local version of strftime seem to be thin wrappers over the standard C function

mkbool() unimplemented. Priority uncertain

asort, asorti. Unimplemented. Medium priority

gensub. Unimplemented, low priority

patsplit, strtonum. Unimplemented, uncertain priority

### Built-in Variables

#### POSIX

Implemented: ARGC, ARGV, ENVIRON, FILENAME, FNR, FS, NF, NR, OFS 

Not Implemented (priority medium-high) ARGIND, CONVFMT, ERRNO, OFMT, ORS, RLENGTH, RS, RSTART, SUBSEP,SYMTAB

Not implemented, priority (medium-low )FUNCTAB

PROCINFO Not implemented, will probably be implemented in stages

GAWK extensions
