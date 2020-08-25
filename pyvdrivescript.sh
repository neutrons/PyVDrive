#!/bin/sh
python setup.py pyuic
python setup.py build

CMDS='' 
for file in "$@" 
do 
  CMDS="$CMDS $file" 
done 

# PYTHONPATH=build/core:$PYTHONPATH build/scripts-2.7/integrate_single_crystal_peaks.py $CMD
# PYTHONPATH=build/core:$PYTHONPATH build/scripts-2.7/chop_single_crystal_run.py $CMDS
PYTHONPATH=build/lib:$PYTHONPATH build/scripts-2.7/focus_single_crystal_run.py $CMDS
