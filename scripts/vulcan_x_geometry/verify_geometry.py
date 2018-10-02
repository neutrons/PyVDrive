# This file is designed to verify the geometry of VULCAN-X working with McVine
# It shall be used inside MantidPlot
import math

Current_Phase = 'Vulcan-X Concept Proof'
Current_Phase = 'Vulcan-X Phase 1'

Bank_Parameter_Dict = {'Vulcan-X Concept Proof': {1: (160, 128),
                                                  2: (160, 128),
                                                  3: (72, 128)},
                       'Vulcan-X Phase 1': {1: (160, 512),
                                            2: (160, 512),
                                            3: (72, 256)}}


def cal_2theta(x, y, z):
    """
    calculate 2-theta angle from source to sample and from sample to detector
    i.e., cos(2theta) = (x, y, z) cdot L1 / |(x, y, z)|*L1
    :param x:
    :param y:
    :param z:
    :return:
    """
    vec_a = (x, y, z)
    vec_b = (0, 0, 43.)

    dot_prod = z * 43.
    cos_2theta = dot_prod / math.sqrt(x**2 + y**2 + z**2) / 43.
    twotheta = math.acos(cos_2theta) * 180. / math.pi

    return twotheta


def main(ws_name):
    """
    :param ws_name
    :return:
    """
    workspace = mtd[ws_name]

    start_ws_index = 0
    for bank_id in sorted(Bank_Parameter_Dict[Current_Phase].keys()):
        num_tubes, num_tube_pixels = Bank_Parameter_Dict[Current_Phase][bank_id]
        end_ws_index = start_ws_index + num_tubes * num_tube_pixels - 1

        # 4 corners
        corner_ws_index_dict = dict()
        corner_ws_index_dict['lower left'] = start_ws_index
        corner_ws_index_dict['upper left'] = start_ws_index + num_tube_pixels - 1
        corner_ws_index_dict['upper right'] = end_ws_index
        corner_ws_index_dict['lower right'] = end_ws_index - num_tube_pixels + 1

        print ('Bank {} Corners:'.format(bank_id))
        for corner in sorted(corner_ws_index_dict.keys()):
            det_id = workspace.getDetector(corner_ws_index_dict[corner]).getID()
            det_pos = workspace.getDetector(corner_ws_index_dict[corner]).getPos()
            print ('{}: Detector ID = {}  @ X = {}, Y = {}, Z= {}'
                   ''.format(corner, det_id, det_pos.X(), det_pos.Y(), det_pos.Z()))
                   
        # center from corner
        sum_x = 0
        sum_y = 0
        sum_z = 0
        for corner in sorted(corner_ws_index_dict.keys()):
            det_pos = workspace.getDetector(corner_ws_index_dict[corner]).getPos()
            sum_x += det_pos.X()
            sum_y += det_pos.Y()
            sum_z += det_pos.Z()
        print ('\tCenter calculated from corners: X = {}, Y = {}, Z = {}'.format(sum_x*0.25, sum_y*0.25, sum_z*0.25))

        # center 4 pixels: general to N*8-pack case, but not N*8 tube case
        center_ws_index_dict = dict()
        if (num_tubes/8) % 2 == 0:
            # even: pick the pack index
            right_pack_id = (num_tubes/8) / 2
            left_pack_id = right_pack_id - 1

            # find center
            center_ws_index_dict['upper left'] = \
                (8 * num_tube_pixels) * left_pack_id + (num_tube_pixels * 7) + num_tube_pixels / 2 + start_ws_index
            center_ws_index_dict['lower left'] = center_ws_index_dict['upper left'] - 1

            center_ws_index_dict['upper right'] = (8 * num_tube_pixels) * right_pack_id + num_tube_pixels / 2 + start_ws_index
            center_ws_index_dict['lower right'] = center_ws_index_dict['upper right'] - 1

        else:
            # odd: pick the middle pack
            middle_pack_id = (num_tubes/8) / 2
            start_pack_tube_index = middle_pack_id * 8

            # find center
            center_ws_index_dict['upper left'] =  start_ws_index + (start_pack_tube_index + 3) * num_tube_pixels + num_tube_pixels / 2
            center_ws_index_dict['lower left'] = center_ws_index_dict['upper left'] - 1
            center_ws_index_dict['upper right'] = center_ws_index_dict['upper left'] + num_tube_pixels
            center_ws_index_dict['lower right'] = center_ws_index_dict['lower left'] + num_tube_pixels
        # END-IF
        print ('Bank {} Center:'.format(bank_id))
        for center in sorted(center_ws_index_dict.keys()):
            det_id = workspace.getDetector(center_ws_index_dict[center]).getID()
            det_pos = workspace.getDetector(center_ws_index_dict[center]).getPos()
            print ('{}: Detector ID = {}  @ X = {}, Y = {}, Z= {}'
                   ''.format(center, det_id, det_pos.X(), det_pos.Y(), det_pos.Z()))

        # calculate the real center
        sum_center_x = 0.
        sum_center_y = 0.
        sum_center_z = 0.
        for center in sorted(center_ws_index_dict.keys()):
            det_pos = workspace.getDetector(center_ws_index_dict[center]).getPos()
            sum_center_x += det_pos.X()
            sum_center_y += det_pos.Y()
            sum_center_z += det_pos.Z()
        # END-FOR
        center_x = sum_center_x / 4.
        center_y = sum_center_y / 4.
        center_z = sum_center_z / 4.
        print ('Bank {} center: X = {}, Y = {}, Z = {}  @ 2theta = {}'
               ''.format(bank_id, center_x, center_y, center_z, cal_2theta(center_x, center_y, center_z)))

        # mask
        detector_id_list = list()
        for pos_name in center_ws_index_dict:
            ws_index_i = center_ws_index_dict[pos_name]
            detector_id_list.append(ws_index_i)
        for pos_name in corner_ws_index_dict:
            ws_index_i = corner_ws_index_dict[pos_name]
            detector_id_list.append(ws_index_i)
        MaskDetectors(Workspace=ws_name, WorkspaceIndexList=detector_id_list)

        # prepare for the next bank
        start_ws_index = end_ws_index + 1
    # END-FOR


main(ws_name='sim_c_vulcan-x')
