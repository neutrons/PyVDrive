#!/bin/sh
# set up path
MANTIDPATH=/home/wzz/Mantid_Project/builds/debug-master/bin:/SNS/users/wzz/Mantid_Project/vulcan-build/bin/
echo $VULCANPATH

CMDS=''
for file in "$@"
do
  CMDS="$CMDS $file"
done

# Step 1: Generate calibration files from cross correlation
# PYTHONPATH=$MANTIDPATH:$PYTHONPATH python vulcan_cal_bank_calibration.py $CMDS

# # Step 2: Analyze the generated calibration file
PYTHONPATH=$VULCANPATH:$PYTHONPATH python vulcan_cal_evalulate_calibration.py $CMDS
# 
# # Step 4: Second round whole instrument calibration
# PYTHONPATH=$VULCANPATH:$PYTHONPATH python vulcan_cal_instrument_calibration.py


# Example:
# ./calibrate_vulcan_detectors.sh --diamond='/SNS/users/wzz/Projects/VULCAN/CalibrationInstrument/Calibration_20180910/raw_dspace_hitogram.nxs'