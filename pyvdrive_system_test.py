#!/bin/sh
python setup.py pyuic
python setup.py build

if [ $1 ]; then
    CMD=$1
else
    CMD=
    echo "1: peak fit, 2: texture, 3: strain stress, 4: manual reduction"
fi

if [ "$1" = "1" ]
then 
	echo "Test peak fitting module"
        PYTHONPATH=build/lib:$PYTHONPATH build/scripts-2.7/peakfitgui_test.py
fi


# Core Test
PYTHONPATH=build/lib:$PYTHONPATH $CMD tests/development/collimator.py


# IDL-VDRIVE Commands
# PYTHONPATH=build/lib:$PYTHONPATH $CMD build/scripts-2.7/vbin_test.py    # Retest
# PYTHONPATH=build/lib:$PYTHONPATH $CMD build/scripts-2.7/chop_reduce_command_test.py
# PYTHONPATH=build/lib:$PYTHONPATH $CMD build/scripts-2.7/vbin_test.py
# PYTHONPATH=build/lib:$PYTHONPATH $CMD build/scripts-2.7/reduction_view_test.py
# PYTHONPATH=build/lib:$PYTHONPATH $CMD build/scripts-2.7/idl_info_test.py
# PYTHONPATH=build/lib:$PYTHONPATH $CMD build/scripts-2.7/idl_view_test.py

# GUI Tests
# PYTHONPATH=build/lib:$PYTHONPATH $CMD build/scripts-2.7/peakfitgui_test.py

# Unit/Concept Tests
# PYTHONPATH=build/lib:$PYTHONPATH $CMD build/scripts-2.7/vulcan_slice_reduce_test.py
