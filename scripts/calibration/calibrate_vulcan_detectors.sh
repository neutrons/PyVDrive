#!/bin/sh
# set up Mantid path
MANTIDPATH=/home/wzz/Mantid_Project/builds/debug-master/bin:/SNS/users/wzz/Mantid_Project/vulcan-build/bin/
echo $VULCANPATH

CMDS=''
for file in "$@"
do
  CMDS="$CMDS $file"
done

# Step 1.1: Generate calibration files from cross correlation including 1-fit calibration and 2-fit calibration
# Step 1.2: Analyze the generated calibration files including number of masked workspaces and the reason
PYTHONPATH=$MANTIDPATH:$PYTHONPATH python vulcan_cal_bank_calibration.py $CMDS

# Step 2
PYTHONPATH=$VULCANPATH:$PYTHONPATH python vulcan_cal_evalulate_calibration.py $CMDS

# Step 3: Second round whole instrument calibration
PYTHONPATH=$VULCANPATH:$PYTHONPATH python vulcan_cal_instrument_calibration.py

# Example:
# ./calibrate_vulcan_detectors.sh --diamond='/SNS/users/wzz/Projects/VULCAN/CalibrationInstrument/Calibration_20180910/raw_dspace_hitogram.nxs'
