import ndav_widgets.NTableWidget as NTableWidget


class LogSelectorTable(NTableWidget.NTableWidget):
    """ Extended table widget for show the K-shift vectors set to the output Fullprof file
    """
    # Table set up
    TableSetup = [('LogName', 'str'),
                  ('Left/Right', 'checkbox'),
                  ('Select', 'checkbox')]

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

    def get_all_items(self):
        """
        blabla
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

        self._iColAxisName = self.TableSetup.index(('LogName', 'str'))
        self._iColLeft = self.TableSetup.index(('Left/Right', 'checkbox'))
        self._iColSelected = self.TableSetup.index(('Select', 'checkbox'))

        self.setColumnWidth(self._iColAxisName, 200)
        self.setColumnWidth(self._iColSelected, 100)

        return
