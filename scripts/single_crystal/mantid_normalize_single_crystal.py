# this script is supposed to run inside Mantid

# -- Section for user to set up
# single crystal experiment
single_ipts_number = 22752
single_run_number = 172254

# vanadium
vanadium_ipts_number = 22752
vanadium_run_number = 172254

# background: Note: match HR/High intensity, 20Hz or 60Hz to vanadium
background_ipts_number = 22752
background_run_number = 172368


# [SECTION OF VANADIUM]
if True:  # Note: change to False if run for another single crystal
    # Load vanadium
    van_nexus = '/SNS/VULCAN/IPTS-{}/nexus/VULCAN_{}.nxs.h5'.format(vanadium_ipts_number, vanadium_run_number)
    raw_van_ws = LoadEventNexus(Filename=van_nexus, OutputWorkspace='VAN_{}'.format(vanadium_run_number))
    bkgd_nexus = '/SNS/VULCAN/IPTS-{}/nexus/VULCAN_{}.nxs.h5'.format(background_ipts_number, background_run_number)
    bkgd_20hz_hr = LoadEventNexus(Filename=bkgd_nexus, OutputWorkspace='BKGD_{}'.format(background_run_number))

    # get proton charge
    van_pc_sum = raw_van_ws.run().getProperty('proton_charge').value.sum()
    bkgd_pc_sum = bkgd_20hz_hr.run().getProperty('proton_charge').value.sum()
    print ('Vanadium proton charge = {}, Background proton charge = {}'
           ''.format(van_pc_sum, bkgd_pc_sum))

    # Get counts on each spectrum:
    van_sum = ConvertToMatrixWorkspace(InputWorkspace='VAN_{}'.format(vanadium_run_number),
                                       OutputWorkspace='SUM_{}'.format(vanadium_run_number))
    bkgd_sum = ConvertToMatrixWorkspace(InputWorkspace='BKGD_{}'.format(background_run_number),
                                        OutputWorkspace='SUM_{}'.format(background_run_number))
    bkgd_sum *= van_pc_sum / bkgd_pc_sum
    van_sum_clean = Minus(van_sum, bkgd_sum, OutputWorkspace='CLEAN_{}-{}'
                                                             ''.format(vanadium_run_number, background_run_number))
    van_sum_clean += 1  # avoid divided by zero exception
    bank3_counts_ws = SumSpectra(InputWorkspace='CLEAN_{}-{}'.format(vanadium_run_number, background_run_number),
                                 OutputWorkspace='Bank3_Counts_{}'.format(vanadium_run_number),
                                 StartWorkspaceIndex=6467)
    van_bank3_counts = bank3_counts_ws.readY(0)[0]
    print ('Vanadium (with background remove): total counts on high angle (3) bank = {}'.format(van_bank3_counts))

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
    smooth_van_bank3 = FFTSmooth(InputWorkspace=raw_van_bank3,
                                 OutputWorkspace='Smoothed_Bank3_{}'.format(vanadium_run_number),
                                 Filter='Butterworth', Params='5,10', IgnoreXBins=True)

    # [SECTION TO NORMALIZE VANADIUM ITSELF for verification]
    Load(Filename=van_nexus, OutputWorkspace='VerifyVanadium')
    # convert to wave length, rebin and normalized by smooth vanadium
    ConvertUnits(InputWorkspace='VerifyVanadium', OutputWorkspace='VerifyVanadium', Target='Wavelength')
    Rebin(InputWorkspace='VerifyVanadium', OutputWorkspace='VerifyVanadium', Params='-0.001')
    Divide(LHSWorkspace='VerifyVanadium', RHSWorkspace=smooth_van_bank3, OutputWorkspace='VerifyVanadium')
    # Convert to dSpacing
    ConvertUnits(InputWorkspace='VerifyVanadium', OutputWorkspace='VerifyVanadium', Target='dSpacing')
    # Divide by counts per pixels
    final = Divide(LHSWorkspace='VerifyVanadium', RHSWorkspace=van_sum_clean, OutputWorkspace='VerifyVanadium')
    # multiply by total counts
    final *= van_bank3_counts

# [SECTION TO NORMALIZE SINGLE CRYSTAL EXPERIMENT]
single_crystal_nexus = '/SNS/VULCAN/IPTS-{}/nexus/VULCAN_{}.nxs.h5'.format(single_ipts_number, single_run_number)
single_ws_name = 'SCX_{}'.format(single_run_number)
Load(Filename=single_crystal_nexus, OutputWorkspace=single_ws_name)
# convert to wave length, rebin and normalized by smooth vanadium
ConvertUnits(InputWorkspace=single_ws_name, OutputWorkspace=single_ws_name, Target='Wavelength')
Rebin(InputWorkspace=single_ws_name, OutputWorkspace=single_ws_name, Params='-0.001')
Divide(LHSWorkspace=single_ws_name, RHSWorkspace=single_ws_name, OutputWorkspace='Single_172240_Norm')
# Convert to dSpacing
ConvertUnits(InputWorkspace=single_ws_name, OutputWorkspace=single_ws_name, Target='dSpacing')
# Divide by counts per pixels
final_single_crystal_ws = Divide(LHSWorkspace=single_ws_name, RHSWorkspace=van_sum_clean, OutputWorkspace=single_ws_name)
# multiply by total counts
final_single_crystal_ws *= van_bank3_counts


