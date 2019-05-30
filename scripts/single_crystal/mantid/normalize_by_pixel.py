# Task: Generate normalization factor/spectra from measured vanadium
# Date: 2019.05.29
# Version: 1.0
# Platform: MantidPlot
# Related script: (prev) generate_vanadium_normalization.py

# Pseudo-code/workflow
# pre-requisite:  vc_front, vc_back, [count_i]
# 1. load run
# 2. convert to wave length space and rebin
# 3. for each pixel:
#   (1) identify tube that it belongs to to determine front or back
#   (2) normalize by vc_front/vc_back and count_i


# tube set up
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


def get_tube_group_id(ws_index):
    column_size = 256
    det_shift = ws_index - 6468
    tube_index = det_shift/column_size
    if tube_index <= 2 or tube_index > 68:
        # mask out
        tube_group = -1
    elif tube_index % 2 == 0:
        # front
        tube_group = 1
    else:
        # back
        tube_group = 2

    return tube_group


def load_process_run(nexus_name, event_ws_name, norm_by_proton_charge, clean_van_ws, wave_length_bin_param,
                     clean_van_count_ws):
    """
    Load, binning in wave length-space
    :param nexus_name:
    :param event_ws_name:
    :return:
    """
    # Load
    LoadEventNexus(Filename=nexus_name, OutputWorkspace=event_ws_name)

    # Normalize in wave length space
    ConvertUnits(InputWorkspace=event_ws_name, OutputWorkspace=event_ws_name,
                 Target='Wavelength', AlignBins=True)
    Rebin(InputWorkspace=event_ws_name, OutputWorkspace=event_ws_name, Params=wave_length_bin_param, FullBinsOnly=True,
          IgnoreBinErrors=True)

    # Normalize
    event_ws = mtd[event_ws_name]

    group1_norm_vec = clean_van_ws.readY(3)
    group2_norm_vec = clean_van_ws.readY(4)

    clean_van_count = clean_van_count_ws.readY(0)

    for ws_index in range(6468, 24900):
        vec_y_i = event_ws.dataY(ws_index)

        group_id = get_tube_group_id(ws_index)
        if group_id == -1:
            vec_y_i /= 1.E10
        elif group_id == 1:
            vec_y_i /= (group1_norm_vec * clean_van_count[ws_index])
        else:
            vec_y_i /= (group2_norm_vec * clean_van_count[ws_index])

        # set value
    # END-FOR

    # convert to d-spacing
    ConvertUnits(InputWorkspace=event_ws_name, OutputWorkspace=event_ws_name,
                 Target='dSpacing', AlignBins=True)
    Rebin(InputWorkspace=event_ws_name, OutputWorkspace=event_ws_name,
          Params='0.3, -0.0003, 3.5')

    return mtd[event_ws_name]


def main():
    # set the previously generated workspaces for normalization
    clean_van_ws = mtd['']
    clean_van_count_ws = mtd['']

    # diamond/general run
    # IPTS-22753, Run 172361, 172362 (background)

    diamond_nexus = '/SNS/VULCAN/IPTS-22753/nexus/VULCAN_172361.nxs.h5'
    diamond_bkgd_nexus = '/SNS/VULCAN/IPTS-22753/nexus/VULCAN_172362.nxs.h5'
    diamond_ws = load_process_run(diamond_nexus, 'diamond_172361_event', True, clean_van_ws, '1.0, -0.05, 5.0',
                                  clean_van_count_ws)
    bkgd_ws = load_process_run(diamond_bkgd_nexus, 'diamond_bkgd', True, clean_van_ws,
                               '1.0, -0.05, 5.0', clean_van_count_ws)

    diamond_ws -= bkgd_ws

    return


main()
