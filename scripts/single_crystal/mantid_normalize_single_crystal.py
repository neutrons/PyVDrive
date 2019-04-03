# This script is supposed to run inside Mantid
# Procedure to process the single crystal data
# 1. normalize by vanadium spectrum (smoothed and processed)
# 2. group to each tube of high angle bank
# 3. export to dSpacing ascii column file
# 4. export the GSAS file


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

# smoothed vanadium
smoothed_van_name = 'SmoothedVanadium'
counts_van_name = 'VanadiumCounts'

# [SECTION: NORMALIZE SINGLE CRYSTAL EXPERIMENT]
single_crystal_nexus = '/SNS/VULCAN/IPTS-{}/nexus/VULCAN_{}.nxs.h5'.format(single_ipts_number, single_run_number)
single_ws_name = 'SCX_{}'.format(single_run_number)
Load(Filename=single_crystal_nexus, OutputWorkspace=single_ws_name)
# convert to wave length, rebin and normalized by smooth vanadium
ConvertUnits(InputWorkspace=single_ws_name, OutputWorkspace=single_ws_name, Target='Wavelength')
Rebin(InputWorkspace=single_ws_name, OutputWorkspace=single_ws_name, Params='-0.001')
Divide(LHSWorkspace=single_ws_name, RHSWorkspace=smoothed_van_name, OutputWorkspace='Single_172240_Norm')
# Convert to dSpacing
ConvertUnits(InputWorkspace=single_ws_name, OutputWorkspace=single_ws_name, Target='dSpacing')
# Divide by counts per pixels
final_single_crystal_ws = Divide(LHSWorkspace=single_ws_name, RHSWorkspace=counts_van_name,
                                 OutputWorkspace=single_ws_name)


# [SECTION: Group the normalized the ]
tubes_ws = SumSpectrum(InputWorkspace=single_ws_name, GroupingWorkspace=group_ws_name,
                       OutputWorkspace='{}_HighAngleTubes'.format(single_run_number))

# [SECTION: Write out the text file]
assert tubes_ws.getAxis(0).getUnit().unitID() == 'dSpacing', 'High angle tube workspace must be dSpacing but not ' \
                                                             '{}'.format(tubes_ws.getAxis(0).getUnit().unitID())
assert tubes_ws.isHistogram() is False, 'Cannot be histogram'

text_buffer = '# X   Tube 1    Tube 2    ....'
vec_x = tubes_ws.readX(0)
for index in range(vec_x.shape[0]):
    text_buffer += '{}\t '.format(vec_x[index])
    for itube in range(72):
        text_buffer += '{}\t '.format(tubes_ws.readY(itube)[index])
    text_buffer += '\n'

ascii_d_name = '{}_dSpacing.data'.format(single_run_number)
ascii_d_file = open(ascii_d_name, 'w')
ascii_d_file.write(text_buffer)
ascii_d_file.close()

# [SECTION: Write out 72 GSAS files]
import pyvdrive
print (pyvdrive)
from pyvdrive.lib import save_vulcan_gsas
saver = save_vulcan_gsas.SaveVulcanGSS(vulcan_ref_name='/SNS/VULCAN/shared/CALIBRATION/2017_8_11_CAL/vdrive_3bank_bin.h5')
ConvertUnit(InputWorkspace=single_ws_name, OutputWorkspace=single_ws_name, Target='TOF')
Rebin(InputWorkspace=single_ws_name, OutputWorkspace=single_ws_name, Params='3000., -0.0003, 70000.')
SaveGSS(InputWorkspace=single_ws_name,
        Filename='{}_tube.gda'.format(single_run_number),
        UseSpectrumNumberAsBankID=True,
        SplitFiles=True)
