#!/bin/sh
python setup.py pyuic
python setup.py build

echo 
MANTIDLOCALPATH=/home/wzz/Mantid_Project/debug/bin/
MANTIDMACPATH=/Users/wzz/MantidBuild/debug/bin/
MANTIDSNSDEBUGPATH=/SNS/users/wzz/Mantid_Project/builds/debug/bin/
MANTIDPATH=$MANTIDMACPATH:$MANTIDLOCALPATH:$MANTIDSNSDEBUGPATH
PYTHONPATH=$MANTIDPATH:$PYTHONPATH
echo "PYTHON PATH: "
echo $PYTHONPATH
echo


if [ $1 ]; then
    CMD=$1
else
    CMD=
    echo "Options: (1) vbin (2) chop (3) view  (4) vpeak  (5) merge  (6) performance test"
    echo "Options: Test all commands: \"all\""
fi

echo "User option: $1"

if [ "$1" = "1" ] || [ "$1" = "all" ] || [ "$1" = "vbin" ]; then
	echo "Test VBIN (1)"
        PYTHONPATH=build/lib:build/lib.linux-x86_64-2.7:$PYTHONPATH ./build/scripts-2.7/idl_vbin_test.py
fi

if [ "$1" = "2" ] || [ "$1" = "all" ]  ; then
	echo "Test CHOP (2): Coming soon"
        PYTHONPATH=build/lib:build/lib.linux-x86_64-2.7:$PYTHONPATH build/scripts-2.7/idl_chop_test.py
fi

if [ "$1" = "3" ] || [ "$1" = "all" ] ; then
	echo "Test VIEW: Not Implemented"
        # PYTHONPATH=build/lib:$PYTHONPATH build/scripts-2.7/idl_view_test.py
fi

if [ "$1" = "4" ]; then
	echo "Test VPEAK"
        # PYTHONPATH=build/lib:$PYTHONPATH build/scripts-2.7/idl_vpeak_test.py
fi

if [ "$1" = "5" ]; then
	echo "Test MERGE"
        # PYTHONPATH=build/lib:$PYTHONPATH build/scripts-2.7/idl_merge_test.py
fi

if [ "$1" = "6" ]; then
	echo "Performance test: combined commands"
        PYTHONPATH=build/lib:build/lib.linux-x86_64-2.7:$PYTHONPATH ./build/scripts-2.7/performance_combined_test.py
fi
