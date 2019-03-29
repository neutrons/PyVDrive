import pyvdrive
from pyvdrive.lib import save_vulcan_gsas
saver = save_vulcan_gsas.SaveVulcanGSS(vulcan_ref_name='/SNS/VULCAN/shared/CALIBRATION/2017_8_11_CAL/vdrive_3bank_bin.h5')

# [SECTION: CREATE GROUPING WORKSPACE FOR HIGH ANGLE TUBES]
# TODO - FILL ME IN
group_ws_name = 'Tube_Grouping'
if not mtd.doesExist('Tube_Grouping'):
    LoadDiffCal(blabla, 'Tube')
    group_ws = mtd[group_ws_name]
    for i_tube in range(72):
        for i_pixel in range(256):
            group_ws.dataY(6468 + 72*i_tube + i_pixel)[0] = i_tube + 1   # group 1 to 72
# END-IF (grouping)

# TODO  [SECTION: for user to set up]
# single crystal experiment
single_ipts_number = 22752
single_run_number = 172254

# background: background of single crystal group
background_ipts_number = 22752
background_run_number = 172368

# [SECTION: NORMALIZE SINGLE CRYSTAL EXPERIMENT]
single_crystal_nexus = '/SNS/VULCAN/IPTS-{}/nexus/VULCAN_{}.nxs.h5'.format(single_ipts_number, single_run_number)
single_ws_name = 'SCX_{}'.format(single_run_number)
ConvertUnits(InputWorkspace=single_ws_name, OutputWorkspace=single_ws_name, Target='Wavelength')
Rebin(InputWorkspace=single_ws_name, OutputWorkspace=single_ws_name, Params='-0.001')