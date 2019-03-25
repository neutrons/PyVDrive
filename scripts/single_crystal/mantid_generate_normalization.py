# This script is supposed to run inside Mantid
# This script is to generate a normalization data set for single crystal
# Normalization algorithm on bank 3
#
# * vanadium count = vanadium count - vanadium background count * van_total_pc / van_background_total_pc
# * smooth bank 3 vanadium in wavelength-space [FIXME with or without] background removed
# * normalized by count on each pixel
# * normalized by total PC

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
raw_van_ws = LoadEventNexus(Filename=van_nexus, OutputWorkspace='VAN_{}'.format(vanadium_run_number))

bkgd_nexus = '/SNS/VULCAN/IPTS-{}/nexus/VULCAN_{}.nxs.h5'.format(background_ipts_number, background_run_number)
van_bkgd_ws_name = 'VAN_BKGD_{}'.format(background_run_number)
van_bkgd_ws = LoadEventNexus(Filename=bkgd_nexus, OutputWorkspace=van_bkgd_ws_name)

# get proton charge
van_pc_sum = raw_van_ws.run().getProperty('proton_charge').value.sum()
bkgd_pc_sum = van_bkgd_ws.run().getProperty('proton_charge').value.sum()
print ('Vanadium proton charge = {}, Background proton charge = {}, Background will be normalized by {}'
       ''.format(van_pc_sum, bkgd_pc_sum, van_pc_sum / bkgd_pc_sum))

# [Calculate counts on each spectrum]
van_count = ConvertToMatrixWorkspace(InputWorkspace='VAN_{}'.format(vanadium_run_number),
                                   OutputWorkspace='VAN_COUNT_{}'.format(vanadium_run_number))
van_count_name = van_count.name()
bkgd_count = ConvertToMatrixWorkspace(InputWorkspace='VAN_BKGD_{}'.format(background_run_number),
                                    OutputWorkspace='VAN_BKGD_COUNT_{}'.format(background_run_number))
bkgd_count *= van_pc_sum / bkgd_pc_sum
van_count_clean = Minus(van_count, bkgd_count, OutputWorkspace='VAN_CLEAN_{}-{}'
                                          ''.format(vanadium_run_number, background_run_number))
van_count_clean_name = van_count_clean.name()

# [Cleaned bank3's counts]
bank3_counts_ws = SumSpectra(InputWorkspace=van_count_clean_name,
                                                    OutputWorkspace='Bank3_CLEAN_Counts_{}'.format(vanadium_run_number),
                                                    StartWorkspaceIndex=6467)
van_bank3_counts = bank3_counts_ws.readY(0)[0]
print ('Vanadium (with background remove): total counts on high angle (3) bank = {}'.format(van_bank3_counts))

van_count_clean += 1  # avoid divided by zero exception

# [Smooth bank 3 vanadium]
# Smooth vanadium for high angle bank
# convert to wave length, rebin, sum spectra on high angle bank and smooth
# NOTE: counts of background spread to each wave length bin is too low. Thus no need to remove background here
raw_van_ws = ConvertUnits(InputWorkspace=raw_van_ws, OutputWorkspace='VAN_{}'.format(vanadium_run_number),
                          Target='Wavelength')
raw_van_ws = Rebin(InputWorkspace=raw_van_ws, OutputWorkspace='VAN_{}'.format(vanadium_run_number),
                                 Params='-0.001')  # -0.01 is too raw
raw_van_bank3 = SumSpectra(InputWorkspace=raw_van_ws,
                           OutputWorkspace='Bank3_{}'.format(vanadium_run_number),
                           StartWorkspaceIndex=6467)

# background workspace
if True:
    van_bkgd_ws = ConvertUnits(InputWorkspace=van_bkgd_ws, OutputWorkspace=van_bkgd_ws_name, Target='Wavelength')
    van_bkgd_ws = Rebin(InputWorkspace=van_bkgd_ws, OutputWorkspace=van_bkgd_ws_name, Params='-0.001')
    van_bkgd_bank3 = SumSpectra(InputWorkspace=van_bkgd_ws_name,
                                                       OutputWorkspace='Background_{}_bank3'.format(background_run_number),
                                                       StartWorkspaceIndex=6467)
    workspace_list.append(van_bkgd_bank3.name())

    # remove background from raw vanadium
    clean_van_bank3 = raw_van_bank3 - van_bkgd_bank3 * van_pc_sum / bkgd_pc_sum

    # smooth
    smooth_van_bank3 = FFTSmooth(InputWorkspace=clean_van_bank3,
                                 OutputWorkspace='Smoothed_Bank3_{}'.format(vanadium_run_number),
                                 Filter='Butterworth', Params='5,10', IgnoreXBins=True)
else:
    smooth_van_bank3 = FFTSmooth(InputWorkspace=raw_van_bank3,
                                 OutputWorkspace='Smoothed_Bank3_{}'.format(vanadium_run_number),
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
workspace_list_str = '{}, {}'.format(raw_van_ws.name(), van_bkgd_ws.name(), van_count_name, bkgd_count_name,
                                     van_count_clean_name)




