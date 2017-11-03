import ndav_widgets.NTableWidget as NTableWidget


class LogSelectorTable(NTableWidget.NTableWidget):
    """ Extended table widget for show the K-shift vectors set to the output Fullprof file
    """
    # Table set up
    TableSetup = [('LogName', 'str'),
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
        print '[DB...BAT] Add rows: {0}'.format(items)
        for item_name in items:
            self.append_row([item_name, False])

        return

    def get_selected_item(self):
        """
        check all the rows to get the selected row
        :except: RuntimeError if there is zero or more than 1 rows are selected
        :return: item name of the row selected
        """
        row_numbers = self.get_selected_rows()
        if len(row_numbers) != 1:
            raise RuntimeError('{0}'.format(len(row_numbers)))

        return self.get_cell_value(row_numbers[0], self._iColAxisName)

    def setup(self):
        """ Set up the table
        :return:
        """
        self.init_setup(self.TableSetup)

        self._iColAxisName = self.TableSetup.index(('LogName', 'str'))
        self._iColSelected = self.TableSetup.index(('Select', 'checkbox'))

        return

