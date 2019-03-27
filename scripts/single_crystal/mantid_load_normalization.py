# This script is supposed to run inside Mantid
# This script is to generate a normalization data set for single crystal
# Normalization algorithm on bank 3
#
# * vanadium count = vanadium count - vanadium background count * van_total_pc / van_background_total_pc
# * smooth bank 3 vanadium in wavelength-space [FIXME with or without] background removed
# * normalized by count on each pixel
# * normalized by total PC
import h5py
import numpy
from matplotlib import pyplot as plt


def detector_view(workspace, file_name):
    """ Generate the detector view for high angle bank and save to a PNG file
    :param workspace:
    :param file_name:
    :return:
    """
    if workspace.getNumberHistograms() == 1:
        # transposed single spectrum counts workspace
        vec_counts = workspace.readY(0)[6468:]
    elif len(workspace.readY(0)) == 1:
        # single Y value counts workspace: transpose
        temp_count_ws = Transpose(workspace)
        vec_counts = temp_count_ws.readY(0) [6468:]
    else:
        # regular multiple spectrum workspace: integrate for each
        vec_counts = numpy.ndarray(shape=(workspace.getNumberHistograms() - 6468, 1), dtype='float')
        for iws in range(6468, workspace.getNumberHistograms()):
            count_i = numpy.sum(workspace.readY(iws))
            vec_counts[iws - 6468] = count_i
    # END-IF

    # plot
    pixel_matrix = vec_counts.reshpace((72, 256))
    pixel_matrix.transpose()
    plt.imshow(pixel_matrix, origin='lower', interpolation='none')
    plt.savefig(file_name)

    return
# END-DEF-FUNCTION


norm_h5_name = 'vanadium_172254_norm.hdf5'
norm_file = h5py.File(norm_h5_name)

smooth_group = norm_file['smoothed spectrum']
vec_wavelength = smooth_group['tof'].value
vec_van = smooth_group['intensity'].value
vec_e = smooth_group['error'].value

# Create a workspace for smoothed vanadium
smoothed_vanadium = CreateWorkspace(DataX=vec_wavelength, DataY=vec_van, DataE=vec_e, NSpec=1,
                                    OutputWorkspace='SmoothedVanadium', UnitX='Wavelength')
smoothed_van_name = smoothed_vanadium.name()
EditInstrumentGeometry(Workspace=smoothed_van_name, SpectrumIDs='1', PrimaryFlightPath=42.,
                       L2='2', Polar='150.', Azimuthal='0.', DetectorIDs='1', InstrumentName='Vulcan_High_Angle')

# Create a workspace for vanadium counts (with background removed)
count_group = norm_file['counts']
counts_vec = count_group['counts']
vec_x = numpy.arange(counts_vec.shape[0])
counts_van_name = 'VanadiumCounts'
counts_ws = CreateWorkspace(DataX=vec_x, DataY=counts_vec, NSpec=1, OutputWorkspace=counts_van_name)
counts_ws = Transpose(counts_ws, OutputWorkspace=counts_van_name)

norm_file.close()

# [SECTION: VERIFICATION VANADIUM]
if True:
    # vanadium: as an option: normalize vanadium
    vanadium_ipts_number = 22752
    vanadium_run_number = 172254
    
    # background: Note: match HR/High intensity, 20Hz or 60Hz to vanadium
    background_ipts_number = 22752
    background_run_number = 172368

    # Load vanadium & create detector view
    van_nexus = '/SNS/VULCAN/IPTS-{}/nexus/VULCAN_{}.nxs.h5'.format(vanadium_ipts_number, vanadium_run_number)
    raw_van_ws = LoadEventNexus(Filename=van_nexus, OutputWorkspace='VAN_{}'.format(vanadium_run_number))
    detector_view(raw_van_ws, '{}_raw.png'.format(vanadium_run_number))
    print ('[INFO] Raw vanadium workspace: # events = {}'.format(raw_van_ws.getNumberEvents()))

    # Load and remove background
    bkgd_nexus = '/SNS/VULCAN/IPTS-{}/nexus/VULCAN_{}.nxs.h5'.format(background_ipts_number, background_run_number)
    background_ws = LoadEventNexus(Filename=bkgd_nexus, OutputWorkspace='BKGD_{}'.format(background_run_number))
    print ('[INFO] Background workspace: # events = {}'.format(background_ws.getNumberEvents()))

    van_pc = raw_van_ws.run().getProperty('proton_charge').value.sum()
    bkgd_pc = background_ws.run().getProperty('proton_charge').value.sum()

    # examine the counts
    raw_van_count_ws = ConvertToMatrix(raw_van_ws)
    bkgd_count_ws = ConvertToMatrix(background_ws)
    raw_van_ws -= bkgd_count_ws * van_pc / bkgd_pc
    detector_view(raw_van_ws, '{}-{}_count.png'.format(vanadium_run_number, background_run_number))

    # now normalize by imported count workspace
    raw_van_count_ws /= counts_ws
    detector_view(raw_van_count_ws, '{}-{}_norm_count.png'.format(vanadium_run_number, background_run_number))

    # remove background
    # normalize
    background_ws *= van_pc / bkgd_pc
    raw_van_ws -= background_ws
    print ('[INFO] Vanadium with background removed: # events = {}'.format(raw_van_ws.getNumberEvents()))
    detector_view(raw_van_ws, '{}-{}.png'.format(vanadium_run_number, background_run_number))

    # normalize
    # convert to wave length, rebin and normalized by smooth vanadium
    norm_ws_name = '{}_Normalized'.format(vanadium_run_number)
    ConvertUnits(InputWorkspace=raw_van_ws, OutputWorkspace=norm_ws_name, Target='Wavelength')
    Rebin(InputWorkspace=norm_ws_name, OutputWorkspace=norm_ws_name, Params='-0.001')
    Divide(LHSWorkspace=norm_ws_name, RHSWorkspace=smoothed_van_name, OutputWorkspace=norm_ws_name)
    # Convert to dSpacing
    ConvertUnits(InputWorkspace=norm_ws_name, OutputWorkspace=norm_ws_name, Target='dSpacing')
    # Divide by counts per pixels
    final = Divide(LHSWorkspace=norm_ws_name, RHSWorkspace=counts_van_name, OutputWorkspace=norm_ws_name)

    detector_view(final, 'Final_Shall_Be_Uniform.png')


