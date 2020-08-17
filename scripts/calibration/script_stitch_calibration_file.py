# this is a standalone, but not standard, script to stitch several calibration file together
import datetime
import mantid.simpleapi as mantid_api
from mantid.api import AnalysisDataService as mtd

# specify the calibration file and reference nexus file
dir1 = '/home/wzz/Projects/VULCAN/DetectorCalibration/20180910'

west_bank_cal_file = os.path.join(dir1, 'VULCAN_calibrate_2018_06_01.h5')
east_bank_cal_file = os.path.join(dir1, 'VULCAN_calibrate_2018_06_01.h5')
high_angle_bank_cal_file = os.path.join(dir1, 'VULCAN_calibrate_2018_09_12.h5')
ref_nexus = '/SNS/VULCAN/IPTS-20863/nexus/VULCAN_165026.nxs.h5'  # any small-enough sized nexus file

# load reference nexus file
ref_ws = mantid_api.Load(Filename=ref_nexus, OutputWorkspace='VulcanReference')

mask_ws_dict = dict()
cal_ws_dict = dict()
group_ws_dict = dict()

# load calibration file
for base_name, cal_file_name in [('west', west_bank_cal_file),
                                 ('east', east_bank_cal_file),
                                 ('high_angle', high_angle_bank_cal_file)]:
    mantid_api.LoadDiffCal(InputWorkspace=ref_ws,
                           Filename=cal_file_name,
                           WorkspaceName=base_name)

    mask_ws_dict[base_name] = mtd['{}_mask'.format(base_name)]
    cal_ws_dict[base_name] = mtd['{}_cal'.format(base_name)]
    group_ws_dict[base_name] = mtd['{}_group'.format(base_name)]
# END-FOR

# stitch calibration workspace
for iws in range(0, 3234):
    # east bank
    cal_ws_dict['high_angle'].setCell(iws, 1, cal_ws_dict['west'].cell(iws, 1))
for iws in range(3234, 6468):
    # east bank
    cal_ws_dict['high_angle'].setCell(iws, 1, cal_ws_dict['east'].cell(iws, 1))

# stitch mask workspace
for iws in range(0, 3234):  # , 6468):
    # east bank
    mask_ws_dict['high_angle'].dataY(iws)[0] = mask_ws_dict['west'].readY(iws)[0]
for iws in range(3234, 6468):
    # high angle bank
    mask_ws_dict['high_angle'].dataY(iws)[0] = mask_ws_dict['east'].readY(iws)[0]
# mask the workspace again

# check number of spectra masked
num_west_masked = 0
for iws in range(0, 3234):
    if mask_ws_dict['high_angle'].readY(iws)[0] > 0.5:
        num_west_masked += 1
num_east_masked = 0
for iws in range(3234, 6468):
    if mask_ws_dict['high_angle'].readY(iws)[0] > 0.5:
        num_east_masked += 1
num_ha_masked = 0
for iws in range(6468, 24900):
    if mask_ws_dict['high_angle'].readY(iws)[0] > 0.5:
        num_ha_masked += 1
print('# Masked West = {}\n# Masked East = {}\n# Masked High Angle = {}\n# Masked In Total = {}'
      ''.format(num_west_masked, num_east_masked, num_ha_masked, num_west_masked+num_east_masked+num_ha_masked))

# for iws in range(24900):
#     if mask_ws_dict['west'].readY(iws)[0] < 0.5:
#         mask_ws_dict['west'].maskDetector(iws)
#     else:
#         mask_ws_dict['west'].maskDetector(iws, -1)

# export
today = datetime.datetime.now()
mantid_api.SaveDiffCal(CalibrationWorkspace=cal_ws_dict['high_angle'],
                       MaskWorkspace=mask_ws_dict['high_angle'],
                       GroupingWorkspace=group_ws_dict['high_angle'],
                       Filename='VULCAN_calibrate_{}_{:02}_{:02}.h5'.format(today.year, today.month, today.day))
