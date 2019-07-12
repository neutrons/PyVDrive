LoadDiffCal(InstrumentName='VULCAN', Filename='/SNS/VULCAN/shared/CALIBRATION/2019_6_27/VULCAN_calibrate_2019_06_27.h5', WorkspaceName='vulcan_standard')
LoadDiffCal(InstrumentName='VULCAN', Filename='/SNS/VULCAN/shared/CALIBRATION/2018_6_1_CAL/VULCAN_calibrate_2018_06_01_27bank.h5', MakeCalWorkspace=False, MakeMaskWorkspace=False, WorkspaceName='vulcan_temp_27banks')
LoadDiffCal(InstrumentName='VULCAN', Filename='/SNS/VULCAN/shared/CALIBRATION/2018_6_1_CAL/VULCAN_calibrate_2018_06_01_7bank.h5', MakeCalWorkspace=False, MakeMaskWorkspace=False, WorkspaceName='vulcan_temp_07banks')


SaveDiffCal(CalibrationWorkspace='vulcan_standard_cal', GroupingWorkspace='vulcan_temp_27banks_group', MaskWorkspace='vulcan_standard_mask', Filename='/SNS/VULCAN/shared/CALIBRATION/2019_6_27/VULCAN_calibrate_2019_06_27_27banks.h5')