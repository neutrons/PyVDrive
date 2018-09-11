#!/bin/sh
# set up path
VULCANPATH = /SNS/users/wzz/Mantid_Project/vulcan-build/bin/
DIAMONDFILE=$CWD/VULCAN_DIAMOND.nxs

CMDS=''
for file in "$@"
do
  CMDS="$CMDS $file"
done

# Step 1: Generate calibration files from cross correlation
PYTHONPATH=$VULCANPATH:$PYTHONPATH python generate_calibration_file.py $DIAMONDFILE

# Step 2: Analyze the generated calibration file
PYTHONPATH=$VULCANPATH:$PYTHONPATH python generate_calibration_file.py

# Step 4: Second round whole instrument calibration
PYTHONPATH=$VULCANPATH:$PYTHONPATH python vulcan_cal_instrument_calibration.py

