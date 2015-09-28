#
# An extension on QTreeView for file system
#
import os

from PyQt4 import QtGui, QtCore
import ndav_widgets.CustomizedTreeView as treeView


class FileSystemTreeView(QtGui.QTreeView):
    """

    """
    def __init__(self, parent):
        """

        :param parent:
        :return:
        """
        QtGui.QTreeView.__init__(self, parent)

        # Selection mode
        self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)

        # Model
        cur_dir = os.path.expanduser('~')
        file_model = QtGui.QFileSystemModel()
        file_model.setRootPath(QtCore.QString(cur_dir))

        self.setModel(file_model)

        return

    def set_root_path(self, root_path):
        """

        :param root_path: root path (i.e., no parent)
        :return:
        """
        # Root path: from model to TreeView
        self.model().setRootPath(root_path)
        idx = self.model().index(root_path)
        self.setRootIndex(idx)

        self.set_current_path(root_path)

        return

    def set_current_path(self, current_path):
        """

        :param current_path:
        :return:
        """
        # Set default path (i.e., current view)
        idx = self.model().index(current_path)
        self.setCurrentIndex(idx)

        return


class VdriveRunManagerTree(treeView.CustomizedTreeView):
    """
    """
    def __init__(self, parent):
        """

        :param parent:
        :return:
        """
        treeView.CustomizedTreeView.__init__(self, parent)

        self.init_setup(['IPTS-Run'])

        # Add actions
        action_add = QtGui.QAction('Add To Reduce', self)
        action_add.triggered.connect(self.do_add_runs)
        self.addAction(action_add)

        # Disable all the actions
        m_actions = self.actions()
        for m_action in m_actions:
            if str(m_action.text()) != 'Info' or str(m_action.text()) != 'Add To Reduce':
                m_action.setEnabled(False)

        self._mainWindow = None

        return

    def add_ipts_runs(self, ipts_number, run_number_list):
        """
        Add runs of on IPTS
        :param ipts_number: it might an ipts number or a directory
        :param run_numbers:
        :return:
        """
        # Check
        assert(isinstance(run_number_list, list))

        # Create main leaf value
        if isinstance(ipts_number, int) is True:
            main_leaf_value = 'IPTS-%d' % ipts_number
        else:
            main_leaf_value = '%s' % str(ipts_number)
        status, message = self.add_main_item(main_leaf_value, False)
        if status is False:
            print '[Log] %s' % message

        # Add runs
        run_number_list.sort()
        for item in run_number_list:
            if isinstance(item, int):
                run_number = item
            elif isinstance(item, tuple):
                run_number = item[0]
            else:
                raise RuntimeError('Item in run number list is neither integer nor tuple but %s!' % str(type(item)))
            child_value = '%d' % run_number
            self.add_child_main_item(main_leaf_value, child_value)

        return

    def get_current_run(self):
        """ Get current run selected by mouse
        :return:
        """
        # Get current index and item
        current_index = self.currentIndex()
        if isinstance(current_index, QtCore.QModelIndex) is False:
            return False, 'Current index is not QModeIndex instance, but %s.' % str(type(current_index))

        assert(isinstance(current_index, QtCore.QModelIndex))

        current_item = self.model().itemFromIndex(current_index)
        if isinstance(current_item, QtGui.QStandardItem) is False:
            return False, 'Current item is not QStandardItem instance, but %s.' % str(type(current_item))
        assert(isinstance(current_item, QtGui.QStandardItem))

        if current_item.parent() is None:
            # Top-level leaf, IPTS number
            return False, 'Top-level leaf for IPTS number'

        try:
            value_str = str(current_item.text())
            run = int(value_str)
        except ValueError:
            return False, 'Unable to convert %s to run number as integer.' % value_str

        return True, run

    def mouseDoubleClickEvent(self, e):
        """ Override event handling method
        """
        status, current_run = self.get_current_run()
        print '[DB] Select run ', current_run

        if self._mainWindow is not None:
            self._mainWindow.set_run(current_run)

        return

    def set_main_window(self, main_window):
        """

        :param main_window:
        :return:
        """
        self._mainWindow = main_window

        return

