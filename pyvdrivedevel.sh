#!/bin/sh
python setup.py pyuic
python setup.py build
CMDS=''
for file in "$@"
do
  CMDS="$CMDS $file"
done

# set up mantid path with python path
MANTIDLOCALPATH=/home/wzz/Mantid_Project/builds/debug-master/bin/
MANTIDMACPATH=/Users/wzz/MantidBuild/debug-stable/bin/
MANTIDSNSPATH=/opt/mantidnightly/bin/
MANTIDPATH=$MANTIDMACPATH:$MANTIDLOCALPATH:$MANTIDSNSPATH
PYTHONPATH=$MANTIDPATH:$PYTHONPATH
echo $PYTHONPATH

PYTHONPATH=build/lib:build/lib.linux-x86_64-2.7:$PYTHONPATH build/scripts-2.7/Lava.py $CMDS
