#!/bin/sh
# set up Mantid path
MANTIDPATH=/home/wzz/Mantid_Project/builds/debug-master/bin:/SNS/users/wzz/Mantid_Project/vulcan-build/bin/
PVPATH=/SNS/users/wzz/Projects/PyVDrive/PyVDrive
echo $VULCANPATH

CMDS=''
for file in "$@"
do
  CMDS="$CMDS $file"
done

pwd

# Step 1.1: Generate calibration files from cross correlation including 1-fit calibration and 2-fit calibration
# Step 1.2: Analyze the generated calibration files including number of masked workspaces and the reason
# PYTHONPATH=$MANTIDPATH:$PVPATH:$PYTHONPATH python ./scripts/calibration/vulcan_cal_instrument_calibration.py --test=0 --nexus=/SNS/VULCAN/IPTS-22752/nexus/VULCAN_171866.nxs.h5 --focus=3 --ref=/SNS/VULCAN/shared/CALIBRATION/2018_9_10_CAL/VULCAN_calibrate_2018_09_12.h5

# Step 2
PYTHONPATH=$VULCANPATH:$PYTHONPATH python ./scripts/calibration/vulcan_cal_evalulate_calibration.py --nexus=/SNS/VULCAN/IPTS-22752/nexus/VULCAN_171866.nxs.h5 --calib=VULCAN_Calibration_2019-1-23_0-15-58_2fit.h5

# Step 3: Second round whole instrument calibration
# PYTHONPATH=$VULCANPATH:$PYTHONPATH python vulcan_cal_instrument_calibration.py

# Example:
# ./calibrate_vulcan_detectors.sh --diamond='/SNS/users/wzz/Projects/VULCAN/CalibrationInstrument/Calibration_20180910/raw_dspace_hitogram.nxs'
