import ndav_widgets.NTableWidget as NTableWidget


class LogSelectorTable(NTableWidget.NTableWidget):
    """ Extended table widget for show the K-shift vectors set to the output Fullprof file
    """
    # Table set up
    TableSetup = [('LogName', 'str'),
                  ('Select', 'checkbox'),
                  ('Left/Right', 'checkbox')
                  ]

    def __init__(self, parent):
        """
        Initialization
        :param parent::

        :return:
        """
        # call super
        super(LogSelectorTable, self).__init__(parent)

        # column index of k-index
        self._iColAxisName = None
        self._iColLeft = None
        self._iColSelected = None

        return

    def add_axis_items(self, items):
        """add axis items
        :param items:
        :return:
        """
        # check input
        assert isinstance(items, list), 'Items {0} must be given in a list but not a {1}.' \
                                        ''.format(items, type(items))

        # add
        for item_name in items:
            self.append_row([item_name, False, False])

        return

    def deselect_all_rows(self):
        """
        de-select all rows
        :return:
        """
        selected_row_list = self.get_selected_rows(True)
        for row_number in selected_row_list:
            self.update_cell_value(row_number, self._iColSelected, False)

        return

    def get_all_items(self):
        """
        get axis name of all the rows
        :return:
        """
        item_list = list()
        num_rows = self.rowCount()
        for i_row in range(num_rows):
            item_name = self.get_cell_value(i_row, self._iColAxisName)
            item_list.append(item_name)

        return item_list

    def get_selected_items(self):
        """
        check all the rows to get the selected row
        :except: RuntimeError if there is zero or more than 1 rows are selected
        :return: 2-tuple.  (1) list of item name. (2) list of main/right axis (True/False)
        """
        row_numbers = self.get_selected_rows()
        if len(row_numbers) == 0:
            raise RuntimeError('There is not row selected')

        item_name_list = list()
        axis_side_list = list()
        for row_index in row_numbers:
            item_name = self.get_cell_value(row_index, self._iColAxisName)
            axis_side = self.get_cell_value(row_index, self._iColLeft)
            item_name_list.append(item_name)
            axis_side_list.append(axis_side)

        return item_name_list, axis_side_list

    def setup(self):
        """ Set up the table
        :return:
        """
        self.init_setup(self.TableSetup)
        self.set_status_column_name('Select')

        self._iColAxisName = self.TableSetup.index(('LogName', 'str'))
        self._iColLeft = self.TableSetup.index(('Left/Right', 'checkbox'))
        self._iColSelected = self.TableSetup.index(('Select', 'checkbox'))

        self.setColumnWidth(self._iColAxisName, 200)
        self.setColumnWidth(self._iColSelected, 100)

        return


class LivePlotYAxisTable(NTableWidget.NTableWidget):
    """
    Table widgets for selected Y axis
    """
    # Table set up
    TableSetup = [('Select', 'checkbox'),
                  ('LogName', 'str'),
                  ('Left/Right', 'checkbox'),
                  ('Min Dspacing', 'float'),
                  ('Max Dspacing', 'float'),
                  ('Normalize', 'checkbox')
                  ]

    def __init__(self, parent):
        """
        Initialization
        :param parent::

        :return:
        """
        # call super
        super(LivePlotYAxisTable, self).__init__(parent)

        # column index of k-index
        self._iColAxisName = None
        self._iColLeft = None
        self._iColSelected = None
        self._iColMinD = None
        self._iColMaxD = None
        self._iColNormByVan = None

        return

    def add_log_item(self, log_name, side):
        """
        add sample log item
        :param log_name:
        :param side:
        :return:
        """
        # check input
        assert isinstance(log_name, str), 'Log name {0} must be given in a string but not a {1}.' \
                                          ''.format(log_name, type(log_name))
        assert isinstance(side, bool), 'Side {0} to add log {1} must be a boolean but not a {1}' \
                                       ''.format(side, log_name, type(side))

        # select/name/side/dmin/dmax/norm by van
        log_name = log_name.split('(')[0].strip()  # clean name
        self.append_row([True, log_name, side, '', '', False])

        return

    def add_peak_parameter(self, peak_info_str, is_main, min_d, max_d, norm_by_van):
        """

        :param peak_info_str:
        :param min_d:
        :param max_d:
        :param norm_by_van:
        :return:
        """
        # TODO check!

        self.append_row([True, peak_info_str, is_main, min_d, max_d, norm_by_van])

        return

    def get_selected_items(self):
        """
        get selected items
        :return: 4-tuple (list, list, list, list)
        """
        item_name_list = list()
        side_list = list()
        peak_range_list = list()
        norm_list = list()

        selected_row_list = self.get_selected_rows(True)
        for row_number in selected_row_list:
            item_name = self.get_cell_value(row_number, self._iColAxisName)
            is_main = self.get_cell_value(row_number, self._iColLeft)
            min_d = self.get_cell_value(row_number, self._iColMinD, allow_blank=True)
            max_d = self.get_cell_value(row_number, self._iColMaxD, allow_blank=True)
            norm_by_van = self.get_cell_value(row_number, self._iColNormByVan)
            print '[DB...BAT] {0} {1}'.format(min_d, max_d)

            item_name_list.append(item_name)
            side_list.append(is_main)
            peak_range_list.append((min_d, max_d))
            norm_list.append(norm_by_van)
        # END-FOR

        return item_name_list, side_list, peak_range_list, norm_list

    def setup(self):
        """ Set up the table
        :return:
        """
        self.init_setup(self.TableSetup)
        self.set_status_column_name('Select')

        self._iColAxisName = self.TableSetup.index(('LogName', 'str'))
        self._iColLeft = self.TableSetup.index(('Left/Right', 'checkbox'))
        self._iColSelected = self.TableSetup.index(('Select', 'checkbox'))
        self._iColMinD = self.TableSetup.index(('Min Dspacing', 'float'))
        self._iColMaxD = self.TableSetup.index(('Max Dspacing', 'float'))
        self._iColNormByVan = self.TableSetup.index(('Normalize', 'checkbox'))

        self.setColumnWidth(self._iColAxisName, 200)
        self.setColumnWidth(self._iColSelected, 80)

        return
