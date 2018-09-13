# this is a standalone, but not standard, script to stitch several calibration file together
import mantid.simpleapi as mantid_api
from mantid.api import AnalysisDataService as mtd

# specify the calibration file and reference nexus file
west_bank_cal_file = ''
east_bank_cal_file = ''
high_angle_bank_cal_file = ''
ref_nexus = ''

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
for iws in range(3234, 6468):
    # east bank
    cal_ws_dict['west'] = do_not_know

# stitch mask workspace
for iws in range(3234, 6468):
    # east bank
    mask_ws_dict['west'].dataY(iws)[0] = mask_ws_dict['east'].readY(iws)[0]
for iws in range(6468, 24900):
    # high angle bank
    mask_ws_dict['west'].dataY(iws)[0] = mask_ws_dict['high_angle'].readY(iws)[0]
# mask the workspace again
for iws in range(24900):
    if mask_ws_dict['west'].readY(iws)[0] < 0.5:
        mask_ws_dict['west'].maskDetector(iws)
    else:
        mask_ws_dict['west'].maskDetector(iws, -1)

# export
import datetime
today = datetime.datetime.now()
mantid_api.SaveDiffCal(CalibrationWorksapce=cal_ws_dict['west'],
                       MaskWorkspace=mask_ws_dict['west'],
                       GroupingWorkspace=group_ws_dict['weest'],
                       Filename='VULCAN_calibrate_{}_{:02}_{:02}.h5'.format(today.year, today.month, today.day))

