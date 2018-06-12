# A collection of methods and constants for VULCAN instrument geometry
import datatypeutility


"""
Definition of instrument detector geometry as constants
Panel 1: 0,    1077; Detector ID: 26250, 27327
Panel 2: 1078, 2155; Detector ID: 27500, 28577
Panel 3: 2156, 3233; Detector ID: 28750, 29827
Panel 4: 3234, 4311; Detector ID: 32500, 33577
Panel 5: 4312, 5389; Detector ID: 33750, 34827
Panel 6: 5390, 6467; Detector ID: 35000, 36077
Panel 6: 6468, 24899; Detector ID: 62500, 80931

"""
# detector range for each panel
VULCAN_PANEL_DETECTORS = {1: {1: {1, 2}},
                          2: {1: (26250, 27327),
                              2: (27500, 28577),
                              3: (28750, 29827),
                              4: (32500, 33577),
                              5: (33750, 34827),
                              6: (35000, 36077),
                              7: (62500, 80931)}}

# number of column of detectors in each panel
VULCAN_PANEL_COLUMN_COUNT = {1: {},  # pre-Ned
                             2: {1: 154,
                                 2: 154,
                                 3: 154,
                                 4: 154,
                                 5: 154,
                                 6: 154,
                                 7: 72}}

# number of rows of detectors in each panel
# high angle bank's panel have rows
VULCAN_PANEL_ROW_COUNT = {1: {},  # pre-Ned
                          2: {1: 7,  # 90-degree banks' panels have 7 rows for each
                              2: 7,
                              3: 7,
                              4: 7,
                              5: 7,
                              6: 7,
                              7: 256}}

VULCAN_PANEL_COLUMN_MAJOR = {1: {},  # pre-nED
                             2: {1: True,
                                 2: True,
                                 3: True,
                                 4: True,
                                 5: True,
                                 6: True,
                                 7: True}}


class VulcanGeometry(object):
    """
    a static class to calculate by retrieving vulcan geometry knowledge from pre-defined constants
    """
    def __init__(self, pre_ned=False):
        """
        initialization to define the type of VULCAN geometry
        :param pre_ned:
        """
        if pre_ned:
            self._generation = 1
        else:
            self._generation = 2

        return

    def get_detector_location(self, detector_id):
        """
        get detector location
        :param detector_id:
        :return:
        """
        # check panel index: because the number of panels are limited, simple brute force search won't be
        # too inefficient
        panel_index = -1
        for panel_index_i in VULCAN_PANEL_DETECTORS[self._generation]:
            first_det_id, last_det_id = VULCAN_PANEL_DETECTORS[self._generation][panel_index_i]
            if first_det_id <= detector_id <= last_det_id:
                panel_index = panel_index_i
                break
        # ENDFOR

        if panel_index < 0:
            raise RuntimeError('Invalid detector ID {0}'.format(detector_id))

        # locate row and column information
        if VULCAN_PANEL_COLUMN_MAJOR[self._generation][panel_index]:
            row_count = VULCAN_PANEL_ROW_COUNT[self._generation][panel_index]
            first_det_id, last_det_id = VULCAN_PANEL_DETECTORS[self._generation][panel_index]
            detector_shift = detector_id - first_det_id
            column_index = detector_shift / row_count
            row_index = detector_shift % row_count

        else:
            # row major
            raise RuntimeError('Row major is not supported')

        return panel_index, row_index, column_index

    def get_detectors_rows_cols(self, det_id_list):
        """
        get the row numbers of the given detector IDs
        :param det_id_list:
        :return:
        """
        datatypeutility.check_list('Detector IDs', det_id_list)

        panel_row_set = set()
        panel_col_set = set()

        for det_id in det_id_list:
            panel_id, row_index, col_index = self.get_detector_location(det_id)
            panel_row_set.add((panel_id, row_index))
            panel_col_set.add((panel_id, col_index))

        return panel_row_set, panel_col_set

    def get_detectors_in_column(self, panel_column_list):
        """

        :param panel_column_list:  a list of 2-tuples
        :return:
        """
        datatypeutility.check_list('Panel index / row index list', panel_column_list)

        det_id_list = list()
        for panel_row_tuple in panel_column_list:
            datatypeutility.check_tuple('Panel index / row index', panel_row_tuple, 2)
            panel_index, row_index = panel_row_tuple

            zero_det_id = VULCAN_PANEL_DETECTORS[self._generation][panel_index][0]
            for col_index in range(VULCAN_PANEL_COLUMN_COUNT[self._generation][panel_index]):
                if VULCAN_PANEL_COLUMN_MAJOR[self._generation][panel_index]:
                    # column major
                    num_rows_per_column = VULCAN_PANEL_ROW_COUNT[self._generation][panel_index]
                    det_id_list.extend(range(zero_det_id + col_index * num_rows_per_column,
                                             zero_det_id + (col_index+1) * num_rows_per_column))
                else:
                    raise NotImplementedError('Row major case is not implemented')
            # END-FOR

        return det_id_list

    def get_detectors_in_row(self, panel_row_list):
        """

        :param panel_row_list: a list of 2-tuples
        :return:
        """
        datatypeutility.check_list('Panel index / row index list', panel_row_list)

        det_id_list = list()
        for panel_row_tuple in panel_row_list:
            datatypeutility.check_tuple('Panel index / row index', panel_row_tuple, 2)
            panel_index, row_index = panel_row_tuple

            zero_det_id = VULCAN_PANEL_DETECTORS[self._generation][panel_index][0]
            for col_index in range(VULCAN_PANEL_COLUMN_COUNT[self._generation][panel_index]):
                if VULCAN_PANEL_COLUMN_MAJOR[self._generation][panel_index]:
                    det_id_i = zero_det_id + col_index * VULCAN_PANEL_ROW_COUNT[self._generation][panel_index] + row_index
                    det_id_list.append(det_id_i)
                else:
                    raise NotImplementedError('Row major case is not implemented')
            # END-FOR

        return det_id_list
