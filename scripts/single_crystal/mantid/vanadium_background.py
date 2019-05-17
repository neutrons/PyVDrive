# This starts from tube 0 to tube 71 with 0-2 and 69-71 are ignored
# It is assumed that tube 0 is at the left edge of the detector with
front_slit_set = [6, 12, 18, 24, 30, 36, 42, 48, 54, 60, 66]
back_away_set = [5, 7, 11, 13, 17, 19, 23, 25, 29, 31, 35, 37, 41, 43, 47, 49, 53, 55, 59, 61, 65, 67]
front_away_set = [4, 8, 10, 14, 16, 20, 22, 26, 28, 32, 34, 38, 40, 44, 46, 50, 52, 56, 58, 62, 64, 68]
back_slit_set = [3, 9, 15, 21, 27, 33, 39, 45, 51, 57, 63]

tube_group_dict = {1: front_slit_set,
                   2: back_away_set,
                   3: front_away_set,
                   4: back_slit_set}


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

    for group in [1, 2, 3, 4]:
        for tube_index in tube_group_dict[group]:
            pixel_id_0 = p0 + tube_index * column_size
            for iws in range(pixel_id_0, pixel_id_0 + column_size):
                group_ws.dataY(iws)[0] = group + 19

    return


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
    LoadEventNexus(Filename=van_nxs, OutputWorkspace=van_ws_name)
    ConvertUnits(InputWorkspace=van_ws_name, OutputWorkspace=van_ws_name,
                 Target='Wavelength', AlignBins=True)
    Rebin(InputWorkspace=van_ws_name, OutputWorkspace=van_ws_name, Params='-0.001', FullBinsOnly=True,
          IgnoreBinErrors=True)

    # Sum spectra by grouping detectors
    grouped_van_name = van_ws_name + '_grouped'
    GroupDetectors(InputWorkspace=van_ws_name, OutputWorkspace=grouped_van_name,
                   CopyGroupingFromWorkspace='vulcan_group')

    # solve the linear equations
    # TODO - TONIGHT 0 - Resume from here!
    # use vector operation
    # TODO - same: create another script/prototype/ to group workspace by 2theta value and normalize

    return

main()

