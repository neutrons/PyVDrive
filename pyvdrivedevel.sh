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
MANTIDSNSDEBUGPATH=/SNS/users/wzz/Mantid_Project/builds/debug/bin/
MANTIDSNSDEBUGPATH=/opt/Mantid/bin/
MANTIDPATH=$MANTIDMACPATH:$MANTIDLOCALPATH:$MANTIDSNSDEBUGPATH
PYTHONPATH=$MANTIDPATH:$PYTHONPATH
echo $PYTHONPATH

PYTHONPATH=build/lib:$PYTHONPATH build/scripts-2.7/Lava.py $CMDS
