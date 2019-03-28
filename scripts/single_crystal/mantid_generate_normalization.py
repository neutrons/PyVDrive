# This script is supposed to run inside Mantid
# This script is to generate a normalization data set for single crystal
# Normalization algorithm on bank 3
#
# * vanadium count = vanadium count - vanadium background count * van_total_pc / van_background_total_pc
# * smooth bank 3 vanadium in wavelength-space [FIXME with or without] background removed
# * normalized by count on each pixel
# * normalized by total PC
#
# NOTE: All workspaces generated in this script will be started with 'CAL_'

# -- Section for user to set up
# vanadium
vanadium_ipts_number = 22752
vanadium_run_number = 172254

# vanadium background: Note: match HR/High intensity, 20Hz or 60Hz to vanadium
background_ipts_number = 22752
background_run_number = 172368

workspace_list = list()  # list of workspaces' names

# [Load vanadium]
van_nexus = '/SNS/VULCAN/IPTS-{}/nexus/VULCAN_{}.nxs.h5'.format(vanadium_ipts_number, vanadium_run_number)
raw_van_ws_name = 'CAL_VAN_{}'.format(vanadium_run_number)
raw_van_ws = LoadEventNexus(Filename=van_nexus, OutputWorkspace=raw_van_ws_name)

bkgd_nexus = '/SNS/VULCAN/IPTS-{}/nexus/VULCAN_{}.nxs.h5'.format(background_ipts_number, background_run_number)
van_bkgd_ws_name = 'CAL_BKGD_{}'.format(background_run_number)
van_bkgd_ws = LoadEventNexus(Filename=bkgd_nexus, OutputWorkspace=van_bkgd_ws_name)

# get proton charge
van_pc_sum = raw_van_ws.run().getProperty('proton_charge').value.sum()
bkgd_pc_sum = van_bkgd_ws.run().getProperty('proton_charge').value.sum()
print ('Vanadium proton charge = {}, Background proton charge = {}, Background will be normalized by {}'
       ''.format(van_pc_sum, bkgd_pc_sum, van_pc_sum / bkgd_pc_sum))

#----------------------------------------------------------------------
# [Calculate counts on each spectrum]
van_count_name = 'CAL_VAN_{}_COUNT'.format(vanadium_run_number)
van_count = ConvertToMatrixWorkspace(InputWorkspace=raw_van_ws_name,
                                     OutputWorkspace=van_count_name)

bkgd_count_name = 'CAL_BKGD_{}_COUNT'.format(background_run_number)
bkgd_count = ConvertToMatrixWorkspace(InputWorkspace=van_bkgd_ws_name,
                                      OutputWorkspace=bkgd_count_name)
bkgd_count *= van_pc_sum / bkgd_pc_sum

van_count_clean_name = 'VAN_CLEAN_{}-{}'.format(vanadium_run_number, background_run_number)
van_count_clean = Minus(van_count, bkgd_count, OutputWorkspace=van_count_clean_name)
# FORCE the minimum count be 1 for normalization
num_zero_neg = 0
for iws in van_count_clean.getNumberHistograms():
    if van_count_clean.readY(iws)[0] < 1.:
        van_count_clean.dataY(iws)[0] = 1.
        if iws >= 6468:
            num_zero_neg += 1
print ('High angle bank: {} pixels have near zero or negative counts after background subtracted'
       ''.format(num_zero_neg))

# [Cleaned bank3's counts]
bank3_counts_ws = SumSpectra(InputWorkspace=van_count_clean_name,
                             OutputWorkspace='CAL_Bank3_CLEAN_Counts_{}'.format(vanadium_run_number),
                             StartWorkspaceIndex=6467)
van_bank3_counts = bank3_counts_ws.readY(0)[0]
print ('Vanadium (with background remove): total counts on high angle (3) bank = {}'.format(van_bank3_counts))

#----------------------------------------------------------------------
# [Smooth bank 3 vanadium]
# Smooth vanadium for high angle bank
# convert to wave length, rebin, sum spectra on high angle bank and smooth
# NOTE: counts of background spread to each wave length bin is too low. Thus no need to remove background here
raw_van_ws = ConvertUnits(InputWorkspace=raw_van_ws_name, OutputWorkspace=raw_van_ws_name,
                          Target='Wavelength')
raw_van_ws = Rebin(InputWorkspace=raw_van_ws_name, OutputWorkspace=raw_van_ws_name, Params='-0.001')  # -0.01 is too raw

raw_van_focus_bank3 = 'CAL_VAN_{}_BANK3_FOCUS'.format(vanadium_run_number)
raw_van_bank3 = SumSpectra(InputWorkspace=raw_van_ws_name,
                           OutputWorkspace=raw_van_focus_bank3,
                           StartWorkspaceIndex=6467)

# background workspace
if True:
    van_bkgd_ws = ConvertUnits(InputWorkspace=van_bkgd_ws, OutputWorkspace=van_bkgd_ws_name, Target='Wavelength')
    van_bkgd_ws = Rebin(InputWorkspace=van_bkgd_ws, OutputWorkspace=van_bkgd_ws_name, Params='-0.001')
    bkgd_focus_bank3_name = 'CAL_Background_{}_Bank3_Focus'.format(background_run_number)
    van_bkgd_bank3 = SumSpectra(InputWorkspace=van_bkgd_ws_name,
                                OutputWorkspace=bkgd_focus_bank3_name,
                                StartWorkspaceIndex=6467)

    # remove background from raw vanadium
    clean_van_bank3 = raw_van_bank3 - van_bkgd_bank3 * van_pc_sum / bkgd_pc_sum

    # smooth
    smooth_van_bank3 = FFTSmooth(InputWorkspace=clean_van_bank3,
                                 OutputWorkspace='CAL_Smoothed_Bank3_{}'.format(vanadium_run_number),
                                 Filter='Butterworth', Params='5,10', IgnoreXBins=True)
else:
    smooth_van_bank3 = FFTSmooth(InputWorkspace=raw_van_bank3,
                                 OutputWorkspace='CAL_Smoothed_Bank3_{}'.format(vanadium_run_number),
                                 Filter='Butterworth', Params='5,10', IgnoreXBins=True)
# END-IF
smooth_van_bank3_name = smooth_van_bank3.name()

# [Normalize the smoothed vanadium spectrum]
print (van_count_clean)
smooth_van_bank3 /= van_bank3_counts

# [Save for result]
import h5py

norm_file = h5py.File('vanadium_{}_norm.hdf5'.format(vanadium_run_number), 'w')

smooth_group = norm_file.create_group('smoothed spectrum')
smooth_group.create_dataset('tof', data=smooth_van_bank3.readX(0))
smooth_group.create_dataset('intensity', data=smooth_van_bank3.readY(0))
smooth_group.create_dataset('error', data=smooth_van_bank3.readE(0))
smooth_group['note'] = 'with background {} removed; normalized by total counts'.format(background_run_number)

count_group = norm_file.create_group('counts')
count_group['note'] = 'with background {} removed'.format(background_run_number)
van_count_clean = Transpose(van_count_clean)
count_group.create_dataset('counts', data=van_count_clean.readY(0))

norm_file.close()

# group workspaces
# [Group workspaces]
workspace_list_str = ''
for ws_name in mtd.getObjectNames():
    if ws_name.startswith('CAL_'):
        workspace_list_str += '{},'.format(ws_name)
workspace_list_str = workspace_list_str[:-1]
GroupWorkspaces(InputWorkspaces=workspace_list_str, OutputWorkspace='Vanadium_Calibration')




