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


def create_template_group_ws():
    """ create a template grouping workspace
    :return:
    """
    # Load
    LoadEventNexus(Filename='/SNS/VULCAN/IPTS-22752/nexus/VULCAN_172254.nxs.h5',
                   OutputWorkspace='vulcan_template', MetaDataOnly=True, LoadLogs=False)
    group_ws_name = 'vulcan_group'
    CreateGroupingWorkspace(InputWorkspace='vulcan_template', GroupDetectorsBy='All',
                            OutputWorkspace=group_ws_name)
    return group_ws_name


def load_process_run(nexus_name, event_ws_name, norm_by_proton_charge):
    """
    Load, binning in d-space and group detectors
    :param nexus_name:
    :param event_ws_name:
    :return:
    """
    LoadEventNexus(Filename=nexus_name, OutputWorkspace=event_ws_name)
    ConvertUnits(InputWorkspace=event_ws_name, OutputWorkspace=event_ws_name,
                 Target='Wavelength', AlignBins=True)
    Rebin(InputWorkspace=event_ws_name, OutputWorkspace=event_ws_name, Params='-0.05', FullBinsOnly=True,
          IgnoreBinErrors=True)

    # Sum spectra by grouping detectors
    grouped_ws_name = event_ws_name + '_grouped'
    GroupDetectors(InputWorkspace=event_ws_name, OutputWorkspace=grouped_ws_name,
                   CopyGroupingFromWorkspace='vulcan_group')

    if norm_by_proton_charge:
        event_ws = mtd[event_ws_name]
        event_ws_pc = event_ws.run().getProperty('proton_charge').value.sum()
        grouped_ws = mtd[grouped_ws_name]
        grouped_ws /= event_ws_pc

    return grouped_ws_name


def remove_background(grouped_van_ws_name, grouped_bkgd_ws_name):

    # remove background
    no_bkgd_ws_name = grouped_van_ws_name + '_bkgd_removed'
    Minus(LHSWorkspace=grouped_van_ws_name,
          RHSWorkspace=grouped_bkgd_ws_name,
          OutputWorkspace=no_bkgd_ws_name)

    # return
    return no_bkgd_ws_name



def set_group_tube(group_ws):
    """ set the group along tubes """
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
    check the grouping file
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
    
    
def get_counts():

    def calculate_counts(ws_name, min_wl, max_wl):
        ConvertUnits(InputWorkspace='van_172254', OutputWorkspace='van_172254', Target='Wavelength', AlignBins=True)
        Rebin(InputWorkspace='van_172254', OutputWorkspace='van_172254',
              Params='0.3,{0},{1},{2},{3},{4},5'.format(min_wl - 0.3, min_wl, max_wl - min_wl, max_wl, 5. - max_wl),
              FullBinsOnly=True, IgnoreBinErrors=True)
        ConvertToMatrixWorkspace(InputWorkspace='masked_van', OutputWorkspace='masked_van')
        Transpose(InputWorkspace='masked_van', OutputWorkspace='masked_van')

        counts_vec = ws.readY(1) / sum_pc   # sum of proton charges

        return counts_vec, ws_name

    LoadEventNexus(Filename='/SNS/VULCAN/IPTS-22752/nexus/VULCAN_172254.nxs.h5', OutputWorkspace='van_172254')
    ConvertUnits(InputWorkspace='van_172254', OutputWorkspace='van_172254', Target='Wavelength', AlignBins=True)
    Rebin(InputWorkspace='van_172254', OutputWorkspace='van_172254', Params='-0.05', FullBinsOnly=True,
          IgnoreBinErrors=True)
    Rebin(InputWorkspace='van_172254', OutputWorkspace='van_172254', Params='0.3,0.7,1,2,3,2,5', FullBinsOnly=True,
          IgnoreBinErrors=True)
    MaskBins(InputWorkspace='van_172254', InputWorkspaceIndexType='WorkspaceIndex', OutputWorkspace='masked_van',
             XMin=1, XMax=3)
    ConvertToMatrixWorkspace(InputWorkspace='masked_van', OutputWorkspace='masked_van')
    Transpose(InputWorkspace='masked_van', OutputWorkspace='masked_van')


def main():
    """
    main
    :return:
    """
    # set up the grouping workspace by template
    group_ws_name = create_template_group_ws()
    group_ws = mtd[group_ws_name]
    set_group_tube(group_ws)
    test_group(group_ws)

    # Load data and rebin
    van_nxs = '/SNS/VULCAN/IPTS-22752/nexus/VULCAN_172254.nxs.h5'
    van_ws_name = 'van_172254'

    bkgd_nxs = ' /SNS/VULCAN/IPTS-22753/nexus/VULCAN_172362.nxs.h5'
    bkgd_ws_name = 'bkgd_172362'

    grouped_van_ws_name = load_process_run(van_nxs, van_ws_name, True)
    grouped_bkgd_ws_name = load_process_run(bkgd_nxs, bkgd_ws_name, True)

    # remove background
    clean_van_ws_name = remove_background(grouped_van_ws_name, grouped_bkgd_ws_name)
    
    # generate the clean-vanadium counts array

    return

main()
