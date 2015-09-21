import ndav_widgets.NTableWidget as NdavWidget


Data_Slicer_Table_Setup = [('Start', 'float'),
                           ('STop', 'float'),
                           ('Status', 'checkbox')]


class DataSlicerSegmentTable(NdavWidget.NTableWidget):
    """
    """
    def __init__(self, parent):
        """
        """
        NdavWidget.NTableWidget.__init__(self, parent)

        return

    def append_start_time(self, time_stamp):
        """

        :param time_stamp:
        :return:
        """
        row_value_list = [time_stamp, '', False]
        # row_type_list = ['float', 'float', 'bool']
        self.append_row(row_value_list) #, row_type_list)

    def setup(self):
        """
        Init setup
        :return:
        """
        self.init_setup(Data_Slicer_Table_Setup)
