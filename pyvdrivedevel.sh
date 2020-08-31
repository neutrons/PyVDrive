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

PYTHONVERSION=$(python --version)
echo $PYTHONVERSION

# Identify pythn path to be 3.6, 3.7 or 3.8
VER='3.8'
SUB37='3.7'
case $PYTHONVERSION in
  *"$SUB37"*)
    echo -n "It's there."
    VER='3.7'
    ;;
esac
SUB36='3.6'
case $PYTHONVERSION in
  *"$SUB36"*)
    echo -n "It's there."
    VER='3.6'
    ;;
esac

PYTHONPATH=build/lib:$PYTHONPATH python3 build/scripts-$VER/Lava.py $CMDS
