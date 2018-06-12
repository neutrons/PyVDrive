#!/bin/sh
python setup.py pyuic
python setup.py build
if [ $1 ]; then
    CMD=$1
else
    CMD=''
fi
PYTHONPATH=build/lib:$PYTHONPATH build/scripts-2.7/integrate_single_crystal_peaks.py $CMD
