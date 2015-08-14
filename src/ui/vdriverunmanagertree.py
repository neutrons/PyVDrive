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

        print 'Hello... I am here!'

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

        return

    def do_delete_run(self):
        """

        :return:
        """
        # TODO - DOC
        print 'Triggered'


    def add_ipts_runs(self, ipts_number, run_number_list):
        """

        :param ipts_number:
        :param run_numbers:
        :return:
        """
        # TODO - Doc
        # TODO - Implement
        if self._runDict.has_key(ipts_number) is False:
            pass

        blabla


    def clear_tree(self):
        """

        :return:
        """
        # TODO - Doc
        # TODO -Implement


    def set_parent(self, logic_parent):
        """
        Parent is the
        :return:
        """
        # TODO - Doc
        # TODO - Implement

