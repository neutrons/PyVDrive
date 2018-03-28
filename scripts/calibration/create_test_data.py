# Create a subset but representative MatrixWorkspace of diamond from VULCAN to test
# cross-correlation
from mantid.simpleapi import LoadNexusProcessed, CropWorkspace, ConjoinWorkspaces, SaveNexusProcessed


def create_partial_diamond(src_nexus_name, target_nexus_name):
    """

    :param src_nexus_name:
    :param target_nexus_name:
    :return:
    """
    # load file
    LoadNexusProcessed(Filname=src_nexus_name, OutputWorkspace='full_diamond')

    # create workspace index list
    ws_index_list = list()

    # N sections on west bank
    ws_index_list.append((0, 3))
    ws_index_list.append((600, 603))
    ws_index_list.append((1200, 1202))
    ws_index_list.append((1800, 1802))
    ws_index_list.append((2400, 2402))
    ws_index_list.append((3200, 3202))

    # N sections on east bank
    base_index = 3234
    ws_index_list.append((base_index+0,    base_index+3))
    ws_index_list.append((base_index+600,  base_index+603))
    ws_index_list.append((base_index+1200, base_index+1202))
    ws_index_list.append((base_index+1800, base_index+1802))
    ws_index_list.append((base_index+2400, base_index+2402))
    ws_index_list.append((base_index+3200, base_index+3202))

    # N sections on high angle bank
    base_index = 6468
    ws_index_list.append((base_index+0,    base_index+3))
    ws_index_list.append((base_index+600,  base_index+603))
    ws_index_list.append((base_index+1200, base_index+1202))
    ws_index_list.append((base_index+1800, base_index+1802))
    ws_index_list.append((base_index+2400, base_index+2402))
    ws_index_list.append((base_index+3200, base_index+3202))

    # Crop and conjoin
    CropWorkspace(InputWorkspace='full_diamond', OutputWorkspace='partial_diamond',
                  StartWorkspaceIndex=ws_index_list[0][0], EndWorkspaceIndex=ws_index_list[0][1])

    for seq in range(1, len(ws_index_list)):
        temp_name = 'temp_{0}'.format(seq)
        # crop
        CropWorkspace(InputWorkspace='full_diamond', OutputWorkspace=temp_name,
                      StartWorkspaceIndex=ws_index_list[seq][0], EndWorkspaceIndex=ws_index_list[seq][1])
        # conjoin
        ConjoinWorkspaces(InputWorkspace1='partial_diamond', InputWorkspace2=temp_name)
    # END-FOR (seq)

    # save/output
    SaveNexusProcessed(InputWorkspace='partial_diamond',
                       Filename=target_nexus_name,
                       Title='Partial 31 hour diamond run')

    return


def main():
    """
    main
    :param argv:
    :return:
    """
    diamond_nexus = \
        '/SNS/users/wzz/Projects/VULCAN/nED_Calibration/Diamond_NeXus/VULCAN_150178_HighResolution_Diamond.nxs'

    create_partial_diamond(diamond_nexus, 'vulcan_partial_diamond.nxs')


if __name__ == '__main__':
    main()