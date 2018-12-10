#!/bin/sh
python setup.py pyuic
python setup.py build

echo 
MANTIDLOCALPATH=/home/wzz/Mantid_Project/debug/bin/
MANTIDMACPATH=/Users/wzz/MantidBuild/debug/bin/
MANTIDSNSDEBUGPATH=/SNS/users/wzz/Mantid_Project/builds/debug/bin/
MANTIDPATH=$MANTIDMACPATH:$MANTIDLOCALPATH:$MANTIDSNSDEBUGPATH
PYTHONPATH=$MANTIDPATH:$PYTHONPATH
echo "PYTHON PATH"
echo $PYTHONPATH
echo


if [ $1 ]; then
    CMD=$1
else
    CMD=
    echo "Options: (1) vbin (2) chop (3) view  (4) vpeak  (5) merge"
fi

if [ "$1" = "1" ] || ["$1" = "vbin"]
then
	echo "Test VBIN"
        PYTHONPATH=build/lib:$PYTHONPATH build/scripts-2.7/idl_vbin_test.py
fi

if [ "$1" = "2" ] || ["$1" = "chop"]
then
	echo "Test CHOP"
        PYTHONPATH=build/lib:$PYTHONPATH build/scripts-2.7/idl_chop_test.py
fi

if [ "$1" = "3" ] || ["$1" = "view"]
then
	echo "Test VIEW"
        PYTHONPATH=build/lib:$PYTHONPATH build/scripts-2.7/idl_view_test.py
fi

if [ "$1" = "4" ] || ["$1" = "vpeak"]
then
	echo "Test VPEAK"
        PYTHONPATH=build/lib:$PYTHONPATH build/scripts-2.7/idl_vpeak_test.py
fi

if [ "$1" = "5" ] || ["$1" = "merge"]
then
	echo "Test MERGE"
        PYTHONPATH=build/lib:$PYTHONPATH build/scripts-2.7/idl_merge_test.py
fi
