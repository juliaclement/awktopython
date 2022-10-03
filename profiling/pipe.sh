#! /bin/bash
echo =========== compiling =========== 
export PYTHONPATH=`pwd`/../code
time python ../code/awkpycc.py -o writepipe.py 'BEGIN {for (i=0; i<12345678; ++i) {print i%4, i;}}'
python ../code/awkpycc.py -o readpipe.py -va=0 '{a+=int($1);} END {print a}'
python ../code/awkpycc.py -Wprofile -o writepipeprof.py 'BEGIN {for (i=0; i<12345678; ++i) {print i%4, i;}}'
python ../code/awkpycc.py -Wprofile -o readpipeprof.py -va=0 '{a+=int($1);} END {print a}'
echo =========== gawk =========== 
time  (gawk 'BEGIN {for (i=0; i<12345678; ++i) {print i%4, i;}}'|gawk -va=0 '{a+=int($1);} END {print a}')
echo =========== pypy3 c+g =========== 
time  (pypy3 ../code/awkpy.py 'BEGIN {for (i=0; i<12345678; ++i) {print i%4, i;}}'|pypy3 ../code/awkpy.py -va=0 '{a+=int($1);} END {print a}')
echo =========== pypy3 compiled =========== 
time  (pypy3 writepipe.py|pypy3 readpipe.py)
echo =========== cpython c+g =========== 
time  (python3 ../code/awkpy.py 'BEGIN {for (i=0; i<12345678; ++i) {print i%4, i;}}'|python3 ../code/awkpy.py -va=0 '{a+=int($1);} END {print a}')
echo =========== cpython compiled =========== 
time  (python3 writepipe.py|python3 readpipe.py)
