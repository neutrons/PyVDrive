import sys

new_calib_file = '/SNS/users/wzz/Projects/VULCAN/Calibration_20180530/vulcan_2fit_v3.h5'
flag = '_2panel'
num_banks = 3


if num_banks == 3:
    template_calib_3bank_file = '/SNS/users/wzz/Projects/VULCAN/Calibration_20180530/VULCAN_calibrate_2018_04_12.h5'
else:
    print ('not define!')
    sys.exit(1)

# Load data
Load(Filename='/SNS/VULCAN/IPTS-21356/nexus/VULCAN_161364.nxs.h5', OutputWorkspace='vulcan_diamond')
# Load old calibration for 3 bank
LoadDiffCal(InputWorkspace='vulcan_diamond', Filename=template_calib_3bank_file, WorkspaceName='vulcan_template')
LoadDiffCal(InputWorkspace='vulcan_diamond', Filename=new_calib_file, WorkspaceName='vulcan{0}'.format(flag))

# Align
AlignDetectors(InputWorkspace='vulcan_diamond', OutputWorkspace='vulcan_diamond', CalibrationWorkspace='vulcan{0}_cal'.format(flag))
Rebin(InputWorkspace='vulcan_diamond', OutputWorkspace='vulcan_diamond', Params='0.5,-0.0003,2')
DiffractionFocussing(InputWorkspace='vulcan_diamond', OutputWorkspace='vulcan_diamond_{0}banks{1}'.format(num_banks, flag), 
                     GroupingWorkspace='vulcan_template_group', PreserveEvents=False)

