#! /bin/bash
echo =========== compiling =========== 
export PYTHONPATH=`pwd`/../code
python ../code/awkpycc.py -o writepipe.py 'BEGIN {for (i=0; i<12345678; ++i) {print i%4, i;}}'
python ../code/awkpycc.py -o readpipe.py -va=0 '{a+=int($1);} END {print a}'
python ../code/awkpycc.py -Wprofile -o writepipeprof.py 'BEGIN {for (i=0; i<12345678; ++i) {print i%4, i;}}'
python ../code/awkpycc.py -Wprofile -o readpipeprof.py -va=0 '{a+=int($1);} END {print a}'
echo =========== running =========== 
pypy3 writepipe.py | pypy3 readpipeprof.py

