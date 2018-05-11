#!/bin/sh
python setup.py pyuic
python setup.py build
if [ $1 ]; then
    CMD=$1
else
    CMD=''
fi
# PYTHONPATH=build/lib:$PYTHONPATH $CMD build/scripts-2.7/chop_reduce_command_test.py
# PYTHONPATH=build/lib:$PYTHONPATH $CMD build/scripts-2.7/vbin_test.py
# PYTHONPATH=build/lib:$PYTHONPATH $CMD build/scripts-2.7/peakfitgui_test.py
PYTHONPATH=build/lib:$PYTHONPATH $CMD build/scripts-2.7/vulcan_slice_reduce_test.py
# PYTHONPATH=build/lib:$PYTHONPATH $CMD build/scripts-2.7/reduction_view_test.py
