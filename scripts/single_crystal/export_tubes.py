#import pyvdrive
#from pyvdrive.lib import save_vulcan_gsas
#gsas_writer = save_vulcan_gsas.SaveVulcanGSS(vulcan_ref_name='/SNS/VULCAN/shared/CALIBRATION/2017_8_11_CAL/vdrive_3bank_bin.h5')


# TODO  [SECTION: for user to set up]
# single crystal experiment
single_ipts_number = 22752
single_run_number = 172254

# background: background of single crystal group
background_ipts_number = 22752
background_run_number = 172368

if True:
    # diamond without mask IPTS-22752, Run 172439, 172441
    single_ipts_number =22752
    single_run_number = 172439
    background_run_number = 172362
 
if False:
    # diamond with mask
    single_ipts_number =22753
    single_run_number = 172361
    background_run_number = 172362

# [SECTION: NORMALIZE SINGLE CRYSTAL EXPERIMENT]
single_crystal_nexus = '/SNS/VULCAN/IPTS-{}/nexus/VULCAN_{}.nxs.h5'.format(single_ipts_number, single_run_number)
single_ws_name = 'SCX_{}'.format(single_run_number)
LoadEventNexus(Filename=single_crystal_nexus, OutputWorkspace=single_ws_name)

# [SECTION: CREATE GROUPING WORKSPACE FOR HIGH ANGLE TUBES]
LoadDiffCal(InputWorkspace=single_ws_name, Filename='/SNS/VULCAN/shared/CALIBRATION/2019_1_20/VULCAN_calibrate_2019_01_21.h5',
            WorkspaceName='VULCAN')
group_ws_name = 'VULCAN_group'
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
            tube_group_ws.dataY(6468 + 256*i_tube + i_pixel)[0] = i_tube + 3   # group 1 to 72
        print (6468 + 256*i_tube + i_pixel-1, i_tube+3)
# END-IF (grouping)

# [Align and Focus]
Rebin(InputWorkspace=single_ws_name, OutputWorkspace=single_ws_name, Params='-0.001')
AlignDetectors(InputWorkspace=single_ws_name, OutputWorkspace=single_ws_name,
               CalibrationWorkspace=calib_ws_name)
DiffractionFocussing(InputWorkspace=single_ws_name, OutputWorkspace='single_focus',
                     GroupingWorkspace=tube_group_name,
                     PreserveEvents=True)
ConvertUnits(InputWorkspace='single_focus', OutputWorkspace='single_focus', Target='dSpacing')
Rebin(InputWorkspace='single_focus', OutputWorkspace='single_focus', Params='0.3,-0.001, 4.0')
ConvertToPointData(InputWorkspace='single_focus', OutputWorkspace='single_focus')
# [SECTION: Write out the text file]
tubes_ws = mtd['single_focus']
assert tubes_ws.getAxis(0).getUnit().unitID() == 'dSpacing', 'High angle tube workspace must be dSpacing but not ' \
                                                             '{}'.format(tubes_ws.getAxis(0).getUnit().unitID())
assert tubes_ws.isHistogramData() is False, 'Cannot be histogram'

text_buffer = '# X   Tube 1    Tube 2    ....\n'
vec_x = tubes_ws.readX(0)
for index in range(vec_x.shape[0]):
    text_buffer += '{}\t '.format(vec_x[index])
    for itube in range(72):
        text_buffer += '{}\t '.format(tubes_ws.readY(2+itube)[index])
    text_buffer += '\n'

ascii_d_name = '{}_dSpacing_Tubes.dat'.format(single_run_number)
ascii_d_file = open(ascii_d_name, 'w')
ascii_d_file.write(text_buffer)
ascii_d_file.close()



"""
import datetime
run_date = datetime.datetime(2019, 1, 1, 0, 0)
text_buffer = gsas_writer.save(diff_ws_name='single_focus', run_date_time=run_date,
                               gsas_file_name='72tube.gda',
                               ipts_number=single_ipts_number,
                               run_number=single_run_number,
                               gsas_param_file_name='vulcan.prm',
                               align_vdrive_bin=True,
                               van_ws_name=None,
                               is_chopped_run=False,
                               write_to_file=True)
"""
