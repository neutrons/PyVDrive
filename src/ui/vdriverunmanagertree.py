from PyQt4 import QtGui, QtCore


class VdriveRunManagerTree(QtGui.QTreeView):
    """
    """
    def __init__(self, parent):
        """

        :param parent:
        :return:
        """
        QtGui.QTreeView.__init__(self, parent)
        self._myParent = parent

        # Set up
        # Tree widget setup for multiple selection
        self.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)

        # Model with 2 columns
        model = QtGui.QStandardItemModel()
        model.setColumnCount(2)
        # model.setDragEnabled(True) Not allowed

        # Header
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'IPTS')
        model.setHeaderData(1, QtCore.Qt.Horizontal, 'Run')

        # Set model and column width
        self.setModel(model)
        self.setColumnWidth(0, 90)
        self.setColumnWidth(1, 60)

        self.setDragEnabled(True)

        # Add action menu: to use right mouse operation for pop-up sub menu
        action = QtGui.QAction('Delete', self)
        action.triggered.connect(self.do_delete_run)
        self.addAction(action)

        self.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

        # Data structure to control the items
        self._dataTree = []  # over all same as model
        self._leafDict = {}  # dictionary for each IPTS number (leaf view)
        self._iptsRowIndexDict = {} # quick index to starting rows of an IPTS

        return

    def do_delete_run(self):
        """
        Delete a run under an IPTS from tree
        :return:
        """
        # Get current item
        index_current_row = int(self.currentIndex())
        ipts_index, run_index = self._check_row(index_current_row)
        if run_index == -1:
            # IPTS: then delete the whole IPTS leaf
            self._delete_ipts(ipts_index)
        else:
            self._delete_run(ipts_index, run_index)

        return

    def add_ipts_runs(self, ipts_number, run_number_list):
        """
        Add runs of on IPTS
        :param ipts_number:
        :param run_numbers:
        :return:
        """
        # Append IPTS to the tree
        if self._iptsRowIndexDict.has_key(ipts_number) is False:
            row_index = len(self._dataTree)
            self._iptsRowIndexDict[ipts_number] = row_index
            item_value = 'IPTS-%d' % ipts_number
            self._dataTree.append(item_value)
            self._leafDict[ipts_number] = []
            self._append_item(row_index, 0, item_value)
        else:
            row_index = self._iptsRowIndexDict[ipts_number]

        # Add runs to the tree
        for run_number in sorted(run_number_list):
            # FIXME - Now it is in appending mode inside IPTS ...
            inner_row_index = len(self._leafDict[ipts_number])
            # Add to tree
            run_row_index = row_index + inner_row_index + 1
            item_value = '%d' % run_number
            self._insert_item(run_row_index, 1, item_value)
            # Update to data structure
            self._dataTree.insert(run_row_index, run_number)
            self._leafDict[ipts_number].append(run_number)
            self._updateIptsRowDict(ipts_number)

        return

    def clear_tree(self):
        """
        Clear the items in the tree
        :return:
        """
        # TODO -Implement
        raise NotImplementedError('Implement ASAP!')

    def set_parent(self, logic_parent):
        """
        Parent is the
        :return:
        """
        # TODO - Doc
        # TODO - Implement

    def _append_item(self, row_index, column_index, item_value):
        """ Append a value to tree
        """
        # New item
        item_main = QtGui.QStandardItem(QtCore.QString(item_value))
        item_main.setCheckable(False)
        self.model().setItem(row_index, column_index, item_main)

        return

    def _delete_ipts(self, ipts_number):
        """

        :param ipts_number:
        :return:
        """
        # TODO - Implement ASAP

        # Propogate the action to parent!
        self._myParent.delete_runs(ipts_number, )

    def _insert_item(self, row_index, column_index, item_value):
        """
        Insert an item
        :param row_index:
        :param column_index:
        :param item_value:
        :return:
        """
