#! /bin/bash
echo =========== compiling =========== 
export PYTHONPATH=`pwd`/../code
python ../code/awkpycc.py -o writepipe.py 'BEGIN {for (i=0; i<12345678; ++i) {print i%4, i;}}'
python ../code/awkpycc.py -o readpipe.py -va=0 '{a+=int($1);} END {print a}'
python ../code/awkpycc.py -Wprofile -o writepipeprof.py 'BEGIN {for (i=0; i<12345678; ++i) {print i%4, i;}}'
python ../code/awkpycc.py -Wprofile -o readpipeprof.py -va=0 '{a+=int($1);} END {print a}'
echo =========== running =========== 
python3 writepipe.py -vawkpy::support_RS=0 | python3 readpipeprof.py -vawkpy::support_RS=0

