import numpy

# Task: Generate normalization factor/spectra from measured vanadium
# Date: 2019.05.29
# Version: 1.0
# Platform: MantidPlot
# Related script: normalize_by_pixel.py

# Pseudo-code/workflow
# 1. sum up vanadium over front tubes and back tubes respectively
# 2. sum up background over front tubes and back tubes respectively
# 3. remove background from vanadium (event workspace)
# 4. convert the clean-vanadium spectra (front- and back-tubes) to wave length space
# 5. normalize the clean-vanadium spectra by number of tubes/pixels
# 6. normalize the clean-vanadium spectra by proton charge
# 7. by observation, smooth clean-vanadium spectra optionally --> vc_front, vc_back
# --- END SECTION 1 ---
# 8. for each pixel: sum counts over wavelength (lambda_start, lambda_stop)  --> count_i
# --- END SECTION 2 ---

front_slit_set = [6, 12, 18, 24, 30, 36, 42, 48, 54, 60, 66]
back_away_set = [5, 7, 11, 13, 17, 19, 23, 25, 29, 31, 35, 37, 41, 43, 47, 49, 53, 55, 59, 61, 65, 67]
front_away_set = [4, 8, 10, 14, 16, 20, 22, 26, 28, 32, 34, 38, 40, 44, 46, 50, 52, 56, 58, 62, 64, 68]
back_slit_set = [3, 9, 15, 21, 27, 33, 39, 45, 51, 57, 63]

# form front and back
front_set = front_slit_set[:]
front_set.extend(front_away_set)
front_set.sort()

back_set = back_slit_set[:]
back_set.extend(back_away_set)
back_set.sort()

tube_group_dict = {1: front_set,
                   2: back_set}

VANADIUM_NEXUS_FILE = '/SNS/VULCAN/IPTS-22752/nexus/VULCAN_172254.nxs.h5'
EMPTY_NEXUS_FILE = '/SNS/VULCAN/IPTS-22753/nexus/VULCAN_172362.nxs.h5'


def create_template_group_ws(vulcan_nexus_file):
    """ create a template grouping workspace for future manipulation
    :return:
    """
    # Load
    LoadEventNexus(Filename=vulcan_nexus_file,
                   OutputWorkspace='vulcan_template', MetaDataOnly=True, LoadLogs=False)
    group_ws_name = 'vulcan_group'
    CreateGroupingWorkspace(InputWorkspace='vulcan_template', GroupDetectorsBy='All',
                            OutputWorkspace=group_ws_name)
    return group_ws_name


def load_process_run(nexus_name, event_ws_name, calib_ws_name, norm_by_proton_charge, pixel_weight_ws_name):
    """
    Load, binning in d-space and group detectors
    :param nexus_name: Workspace will be aligned with unit conversion and rebinning (optionally)
    :param event_ws_name:
    :param norm_by_proton_charge: proton charge normalization will be only run upon focused workspace
    :param pixel_weight_ws_name: name of workspace containing pixel weight
    :return:
    """
    # Load, convert to dSpacing and rebin
    if nexus_name:
        LoadEventNexus(Filename=nexus_name, OutputWorkspace=event_ws_name)

    # Print out information for input workspace
    input_ws = mtd[event_ws_name]
    print ('[INFO] Input {} has {} spectra'.format(event_ws_name, input_ws.getNumberHistograms()))

    if calib_ws_name:
        AlignDetectors(InputWorkspace=event_ws_name, OutputWorkspace=event_ws_name,
                       CalibrationWorkspace=calib_ws_name)

    ConvertUnits(InputWorkspace=event_ws_name, OutputWorkspace=event_ws_name,
                 Target='Wavelength', AlignBins=True)
    Rebin(InputWorkspace=event_ws_name, OutputWorkspace=event_ws_name, Params='0.1, -0.05, 5.0', FullBinsOnly=True,
          IgnoreBinErrors=True)

    # weight
    if pixel_weight_ws_name:
        curr_ws_name = event_ws_name + '_Weighted'
        Normalize_Workspace_Pixel_Counts(event_ws_name, curr_ws_name, pixel_weight_ws_name)

    else:
        curr_ws_name = event_ws_name

    # Sum spectra by grouping detectors
    grouped_ws_name = curr_ws_name.replace('Raw', 'Grouped')
    GroupDetectors(InputWorkspace=curr_ws_name, OutputWorkspace=grouped_ws_name,
                   CopyGroupingFromWorkspace='vulcan_group')

    if norm_by_proton_charge:
        event_ws = mtd[event_ws_name]
        event_ws_pc = event_ws.run().getProperty('proton_charge').value.sum()
        grouped_ws = mtd[grouped_ws_name]
        grouped_ws /= event_ws_pc

    return grouped_ws_name


def remove_background(grouped_van_ws_name, grouped_bkgd_ws_name):

    # remove background
    no_bkgd_ws_name = grouped_van_ws_name + '_Clean'
    Minus(LHSWorkspace=grouped_van_ws_name,
          RHSWorkspace=grouped_bkgd_ws_name,
          OutputWorkspace=no_bkgd_ws_name)

    # return
    return no_bkgd_ws_name


def set_high_angle_front_back_group(group_ws):
    """
    Set the pixels to group according to whether they are at front or back columns
    Rule:
     - West: 10
     - East: 11
     - High angle front: 20
     - High angle back: 21
    :param group_ws:
    :return:
    """
    # west
    for iws in range(0, 3234):
        group_ws.dataY(iws)[0] = 10
    # east
    for iws in range(3234, 6468):
        group_ws.dataY(iws)[0] = 11
    # high angle per tubes
    p0 = 6468  # pixel ID 0 for high angle bank
    column_size = 256

    for group in [1, 2]:
        for tube_index in tube_group_dict[group]:
            pixel_id_0 = p0 + tube_index * column_size
            for iws in range(pixel_id_0, pixel_id_0 + column_size):
                group_ws.dataY(iws)[0] = group + 19

    return


def test_group(group_ws=None):
    """
    check the grouping file by printing out the number of pixels of each group
    :return:
    """
    if group_ws is None:
        group_ws = mtd['vulcan_group']
    det_group_dict = dict()

    for iws in range(group_ws.getNumberHistograms()):
        group_id = int(group_ws.readY(iws)[0] + 0.0001)
        if group_id not in det_group_dict:
            det_group_dict[group_id] = list()
        det_group_dict[group_id].append(iws)
    # END

    for group_id in sorted(det_group_dict.keys()):
        print ('{}: {}'.format(group_id, len(det_group_dict[group_id])))

    return
    
    
def calculate_vanadium_counts(van_ws_name, bkgd_ws_name, min_lambda, max_lambda):
    """ Calculate the cleaned vanadium counts per pixels within a given range of wave length
    :param van_ws_name:
    :param bkgd_ws_name:
    :param min_lambda:
    :param max_lambda
    :return: name of a MatrixWorkspace containing counts
    """
    def calculate_counts(ws_name, min_wl, max_wl):
        """
        calculate counts of each pixel within a given range of wave length
        and normalized by proton charge
        :param ws_name: workspace name
        :param min_wl:
        :param max_wl:
        :return:
        """
        out_ws_name = '{}_counts'.format(ws_name)

        # rebin in range of given wave length
        ConvertUnits(InputWorkspace=ws_name, OutputWorkspace=ws_name, Target='Wavelength', AlignBins=True)
        Rebin(InputWorkspace=ws_name, OutputWorkspace=ws_name,
              Params='0.3,{0},{1},{2},{3},{4},5'.format(min_wl - 0.3, min_wl, max_wl - min_wl, max_wl, 5. - max_wl),
              FullBinsOnly=True, IgnoreBinErrors=True)
        ConvertToMatrixWorkspace(InputWorkspace=ws_name, OutputWorkspace=out_ws_name)
        Transpose(InputWorkspace=out_ws_name, OutputWorkspace=out_ws_name)

        # normalize by counts
        sum_pc = mtd[ws_name].run().getProperty('proton_charge').value.sum()

        count_ws = mtd[out_ws_name]
        count_ws /= sum_pc

        return out_ws_name

    van_count_ws_name = calculate_counts(van_ws_name, min_lambda, max_lambda)
    bkgd_count_ws_name = calculate_counts(bkgd_ws_name, min_lambda, max_lambda)

    # clean counts
    van_count_ws = mtd[van_count_ws_name]
    bkgd_count_ws = mtd[bkgd_count_ws_name]
    clean_van_count_ws = van_count_ws - bkgd_count_ws

    clean_van_count_name = '{}_clean_count'.format(van_ws_name)
    RenameWorkspace(InputWorkspace=clean_van_count_ws, OutputWorkspace=clean_van_count_name)

    return clean_van_count_name


def calculate_pixel_count_weight(clean_van_count_name, group_ws_name):
    """
    Calculate per pixel's weight based on pure/clean vanadium counts.
    The maximum count (per pixel) in high angle bank is defined as 1.
    :param clean_van_count_name:
    :return:
    """
    clean_van_ws = mtd[clean_van_count_name]
    counts_vec = clean_van_ws.readY(1)  # spectrum 2 (ws-index 1) is the count from 1A to 3A
    group_ws = mtd[group_ws_name]

    # calculate the weight
    max_count = numpy.max(counts_vec[6468:])  # minimum factor will be 1

    weight_vec = numpy.zeros(shape=(24900,), dtype='float')

    # do not touch east and west bank (weight = 1)
    weight_vec[:6468] += 1.

    # do it high angle bank
    counts = 0
    for iws in range(6468, 24900):
        if group_ws.readY(iws)[0] < 0.5:  # flagged
            weight_vec[iws] = 0.  # mask
        elif counts_vec[iws] < 1.E-21:
            print ('{} is too small or close to zero'.format(iws))
            counts += 1
        else:
            # TODO - Still working on this
            weight_vec[iws] = 1. / counts_vec[iws]
    # END-FOR

    print ('{} pixels are masked'.format(counts))
    print (clean_van_ws.readX(0).shape)
    print (weight_vec.shape)
    CreateWorkspace(DataX=clean_van_ws.readX(0), DataY=weight_vec, NSpec=1, OutputWorkspace='Pixel_Weights')

    return 'Pixel_Weights'


def generate_normalization():
    """ Generate normalization workspace/file from vanadium and background (empty)
    :return:
    """
    # Input setup
    van_nxs = VANADIUM_NEXUS_FILE
    van_ws_name = 'Vanadium_Raw'

    bkgd_nxs = EMPTY_NEXUS_FILE
    bkgd_ws_name = 'Background_Raw'

    # define the range of wavelength for valid counts
    min_lambda = 1.0
    max_lambda = 3.0

    # Load calibration
    LoadDiffCal(InstrumentName='vulcan',
                Filename='/SNS/VULCAN/shared/CALIBRATION/2019_1_20/VULCAN_calibrate_2019_01_21.h5',
                WorkspaceName='vulcan')
    calibration_ws_name = 'vulcan_cal'

    # set up the grouping workspace by template
    group_ws_name = create_template_group_ws(van_nxs)
    group_ws = mtd[group_ws_name]
    set_high_angle_front_back_group(group_ws)
    test_group(group_ws)

    # load vanadium and group
    grouped_van_ws_name = load_process_run(van_nxs, van_ws_name, calibration_ws_name, True, None)
    # load background and group
    grouped_bkgd_ws_name = load_process_run(bkgd_nxs, bkgd_ws_name, calibration_ws_name, True, None)

    # remove background
    clean_van_ws_name = remove_background(grouped_van_ws_name, grouped_bkgd_ws_name)
    print ('[OUT] Grouped vanadium with background removed: {}'.format(clean_van_ws_name))
    
    # generate the clean-vanadium counts array
    # print (van_ws_name, bkgd_ws_name)
    clean_van_count_name = calculate_vanadium_counts(van_ws_name, bkgd_ws_name, min_lambda, max_lambda)
    print ('[OUT] {} Spectrum 2 contains counts on each pixels between 1 and 3 A (normalized)'
           .format(clean_van_count_name))

    # Normalize each pixels by counts and re-group
    counts_weight_ws_name = calculate_pixel_count_weight(clean_van_count_name)
    # whether counts_weight_ws_name is Pixel_Weights???

    # Process vanadium raw again
    load_process_run(None, 'Vanadium_RAW', None, True, counts_weight_ws_name)

    return


generate_normalization()
