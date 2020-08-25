#!/bin/sh
python3 setup.py pyuic
python3 setup.py build
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

PYTHONPATH=build/lib:$PYTHONPATH python3.6 build/scripts-3.7/Lava.py $CMDS
