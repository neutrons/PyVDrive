# This script is supposed to run inside Mantid
# This script is to generate a normalization data set for single crystal
# Normalization algorithm on bank 3
#
# * vanadium count = vanadium count - vanadium background count * van_total_pc / van_background_total_pc
# * smooth bank 3 vanadium in wavelength-space [FIXME with or without] background removed
# * normalized by count on each pixel
# * normalized by total PC

norm_h5_name = ''
norm_file = h5py.File(norm_h5_name)

smooth_group = norm_file['smoothed spectrum']
vec_d = smooth_group['d'].value
vec_van = smooth_group['intensity'].value
vec_e = smooth_group['error'].value

# smoothed vanadium
smoothed_vanadium = CreateWorkspace(DataX=vec_d, DataY=vec_van, DataE=vec_e, NSpec=1, OutputWorkspace='SmoothedVanadium')
smoothed_van_name = smoothed_vanadium.name()
EditInstrument(InputWorkspace=smoothed_van_name, SpectraList='0', L1=instrument_group['L1'].value,
               L2=instrument_group['L2'].value, Polar=blabla)

# counts (no background)
count_group = norm_file['counts']
counts_vec = count_group['counts']
vec_x = numpy.arange(counts_vec.shape[0])
counts_van_name = 'VanadiumCounts'
counts_ws = CreateWorkspace(DataX=vec_x, DataY=counts_vec, NSpec=1, OutputWorkspace=counts_van_name)
counts_ws = Transpose(counts_ws)

norm_file.close()

# [SECTION: VERIFCATION VANADIUM]
if True:
    # vanadium: as an option: normalize vanadium
    vanadium_ipts_number = 22752
    vanadium_run_number = 172254
    
    # background: Note: match HR/High intensity, 20Hz or 60Hz to vanadium
    background_ipts_number = 22752
    background_run_number = 172368

    # Load vanadium
    van_nexus = '/SNS/VULCAN/IPTS-{}/nexus/VULCAN_{}.nxs.h5'.format(vanadium_ipts_number, vanadium_run_number)
    raw_van_ws = LoadEventNexus(Filename=van_nexus, OutputWorkspace='VAN_{}'.format(vanadium_run_number))
    bkgd_nexus = '/SNS/VULCAN/IPTS-{}/nexus/VULCAN_{}.nxs.h5'.format(background_ipts_number, background_run_number)
    bkgd_20hz_hr = LoadEventNexus(Filename=bkgd_nexus, OutputWorkspace='BKGD_{}'.format(background_run_number))
    # [SECTION TO NORMALIZE VANADIUM ITSELF for verification]
    Load(Filename=van_nexus, OutputWorkspace='VerifyVanadium')
    # convert to wave length, rebin and normalized by smooth vanadium
    ConvertUnits(InputWorkspace='VerifyVanadium', OutputWorkspace='VerifyVanadium', Target='Wavelength')
    Rebin(InputWorkspace='VerifyVanadium', OutputWorkspace='VerifyVanadium', Params='-0.001')
    Divide(LHSWorkspace='VerifyVanadium', RHSWorkspace=smoothed_van_name, OutputWorkspace='VerifyVanadium')
    # Convert to dSpacing
    ConvertUnits(InputWorkspace='VerifyVanadium', OutputWorkspace='VerifyVanadium', Target='dSpacing')
    # Divide by counts per pixels
    final = Divide(LHSWorkspace='VerifyVanadium', RHSWorkspace=counts_van_name, OutputWorkspace='VerifyVanadium')


