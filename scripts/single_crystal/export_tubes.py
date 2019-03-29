import pyvdrive
from pyvdrive.lib import save_vulcan_gsas
gsas_writer = save_vulcan_gsas.SaveVulcanGSS(vulcan_ref_name='/SNS/VULCAN/shared/CALIBRATION/2017_8_11_CAL/vdrive_3bank_bin.h5')



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
LoadEventNeXus(Filename=single_crystal_nexus, OutputWorkspace=single_ws_name)

# [SECTION: CREATE GROUPING WORKSPACE FOR HIGH ANGLE TUBES]
LoadDiffCal(InputWorkspace=single_ws_name, Filename='VULCAN_calibrate_2019_01_21',
            WorkspaceName='VULCAN_')
group_ws_name = 'VULCAN_Grouping'
calib_ws_name = 'VULCAN_Cal'
tube_group_name = 'VULCAN_Tube_Grouping'
CloneWorkspace(InputWorkspace=group_ws_name, OutputWorkspace=tube_group_name)
tube_group_ws = mtd[tube_group_name]
for iws in (0, 3234):
    tube_group_ws.dataY(iws)[0] = 1
for iws in (3234, 6468):
    tube_group_ws.dataY(iws)[0] = 2
for i_tube in range(72):
        for i_pixel in range(256):
            tube_group_ws.dataY(6468 + 72*i_tube + i_pixel)[0] = i_tube + 3   # group 1 to 72
# END-IF (grouping)

# [Align and Focus]
ConvertUnits(InputWorkspace=single_ws_name, OutputWorkspace=single_ws_name, Target='dSpacing')
Rebin(InputWorkspace=single_ws_name, OutputWorkspace=single_ws_name, Params='-0.001')
AlignDetectors(InputWorkspace=single_ws_name, OutputWorkspace=single_ws_name,
               CalibrationWorkspace=calib_ws_name)
DiffractionFocussing(InputWorkspace=single_ws_name, OutputWorkspace='single_focus',
                     GroupingWorkspace=tube_group_name,
                     PreserveEvents=False)

text_buffer = gsas_writer.save(diff_ws_name='single_focussingle_focus', run_date_time='today',
                               gsas_file_name='72tube.gda',
                               ipts_number=single_ipts_number,
                               run_number=single_run_number,
                               gsas_param_file_name='vulcan.prm',
                               align_vdrive_bin=True,
                               van_ws_name=None,
                               is_chopped_run=False,
                               write_to_file=True)
