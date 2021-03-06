#
# An extension on QTreeView for file system
#
import os

try:
    import qtconsole.inprocess  # noqa: F401
    from PyQt5 import QtCore
    from PyQt5.QtWidgets import QTreeView, QAbstractItemView, QFileSystemModel, QAction
    from PyQt5.QtGui import QStandardItem
except ImportError:
    from PyQt4 import QtCore
    from PyQt4.QtGui import QTreeView, QAbstractItemView, QFileSystemModel, QStandardItem
    from PyQt4.QtGui import QAction
from pyvdrive.interface.gui.ndav_widgets import CustomizedTreeView


class FileSystemTreeView(QTreeView):
    """Tree view for file system
    """
    def __init__(self, parent):
        """

        :param parent:
        :return:
        """
        QTreeView.__init__(self, parent)

        # Selection mode
        self.setSelectionMode(QAbstractItemView.SingleSelection)

        # Model
        cur_dir = os.path.expanduser('~')
        file_model = QFileSystemModel()
        # file_model.setRootPath(QtCore.QString(cur_dir))
        file_model.setRootPath(str(cur_dir))

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


class SinglePeakFitManageTree(CustomizedTreeView.CustomizedTreeView):
    """
    Extended tree view widgets to manage single peak fit runs
    """
    def __init__(self, parent):
        """
        :param parent:
        :return:
        """
        # Check requirements:
        assert parent is not None

        # Initialize parent
        CustomizedTreeView.CustomizedTreeView.__init__(self, parent)

        self.init_setup(['IPTS-Run'])

        # Add actions
        action_add = QAction('Load', self)
        action_add.triggered.connect(self.do_load_run)
        self.addAction(action_add)

        # Review all the actions
        for action in self.actions():
            action.setEnabled(True)

        self._mainWindow = parent

        return

    def add_ipts_runs(self, ipts_number, run_number_list):
        """
        Add runs of on IPTS
        :param ipts_number: it might an ipts number or a directory
        :param run_number_list:
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
            print('[Log] %s' % message)

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

    def do_load_run(self):
        """
        Add selected runs
        :return:
        """
        item_list = self.get_selected_items()
        run_list = list()

        for item in item_list:
            run_str = str(item.text())
            try:
                run = int(run_str)
                run_list.append(run)
            except ValueError as error:
                print('[Error] Unable to convert run item with text %s to integer due to %s.' % (run_str, str(error)))
        # END-FOR

        # sort
        run_list.sort()

        # set values
        # FIXME - Better to use signals???
        assert self._mainWindow is not None
        self._mainWindow.load_runs(run_list)

        return run_list

    def get_current_run(self, allow_str=False):
        """ Get current run selected by mouse
        note: if multiple items are selected,
          (1) currentIndex() returns the first selected item
          (2) selectedIndexes() returns all the selected items
        :param allow_str:
        :return: 2-tuple: status, run number in integer or data key in string
        """
        # Get current index and item
        current_index = self.currentIndex()
        if isinstance(current_index, QtCore.QModelIndex) is False:
            return False, 'Current index is not QModelIndex instance, but %s.' % str(type(current_index))

        assert(isinstance(current_index, QtCore.QModelIndex))

        current_item = self.model().itemFromIndex(current_index)
        if isinstance(current_item, QStandardItem) is False:
            return False, 'Current item is not QStandardItem instance, but %s.' % str(type(current_item))
        assert(isinstance(current_item, QStandardItem))

        if current_item.parent() is None:
            # Top-level leaf, IPTS number
            return False, 'Top-level leaf for IPTS number'

        # convert to integer
        value_str = str(current_item.text())
        if value_str.isdigit():
            # convert to integer if it can be converted to an integer
            run = int(value_str)
        elif allow_str:
            # return in string/data key format if user allows a return as a string
            run = value_str
        else:
            # otherwise...
            return False, 'Unable to convert %s to run number as integer.' % value_str

        return True, run

    def mouseDoubleClickEvent(self, e):
        """ Override event handling method
        """
        status, current_run = self.get_current_run(allow_str=True)

        if self._mainWindow is not None:
            print('[INFO] Load and plot data with key = %s.' % str(current_run))
            self._mainWindow.plot_reduced_data(current_run)

        return

    def set_main_window(self, main_window):
        """

        :param main_window:
        :return:
        """
        self._mainWindow = main_window

        return


class VdriveRunManagerTree(CustomizedTreeView.CustomizedTreeView):
    """
    """
    def __init__(self, parent):
        """

        :param parent:
        :return:
        """
        CustomizedTreeView.CustomizedTreeView.__init__(self, parent)

        self.init_setup(['IPTS-Run'])

        # Add actions
        action_add = QAction('Add To Reduce', self)
        action_add.triggered.connect(self.do_add_runs)
        self.addAction(action_add)

        # Disable all the actions
        m_actions = self.actions()
        for m_action in m_actions:
            if str(m_action.text()) != 'Info' and str(m_action.text()) != 'Add To Reduce':
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
            print('[Log] %s' % message)

        # Add runs
        run_number_list.sort()
        for item in run_number_list:
            if isinstance(item, int):
                run_number = item
            elif isinstance(item, dict):
                run_number = item['run']
            else:
                raise RuntimeError('Item in run number list is not dictionary but is %s!' % str(type(item)))
            child_value = '%d' % run_number
            print('Main leaf value = ', main_leaf_value)
            self.add_child_main_item(main_leaf_value, child_value)

        return

    def do_add_runs(self):
        """
        Add selected runs
        :return:
        """
        item_list = self.get_selected_items()
        run_list = list()

        for item in item_list:
            run_str = str(item.text())
            try:
                run = int(run_str)
                run_list.append(run)
            except ValueError as val_err:
                print('[Error] Unable to convert run item with text {} to integer as {}'.format(run_str, val_err))
        # END-FOR

        # sort
        run_list.sort()

        # set values
        # FIXME - Better to use signals???
        if self._mainWindow is not None:
            self._mainWindow.set_selected_runs(run_list)

        return run_list

    def get_current_run(self):
        """ Get current run selected by mouse
        note: if multiple items are selected,
          (1) currentIndex() returns the first selected item
          (2) selectedIndexes() returns all the selected items
        :return: status, run number in integer
        """
        # Get current index and item
        current_index = self.currentIndex()
        if isinstance(current_index, QtCore.QModelIndex) is False:
            return False, 'Current index is not QModelIndex instance, but %s.' % str(type(current_index))

        assert(isinstance(current_index, QtCore.QModelIndex))

        current_item = self.model().itemFromIndex(current_index)
        if isinstance(current_item, QStandardItem) is False:
            return False, 'Current item is not QStandardItem instance, but %s.' % str(type(current_item))
        assert(isinstance(current_item, QStandardItem))

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
        self.do_add_runs()

        # status, current_run = self.get_current_run()
        # if self._mainWindow is not None:
        #     # TODO/FIXME - 'VdriveMainWindow' object has no attribute 'set_run'
        #     self._mainWindow.set_run(current_run)

        return

    def set_main_window(self, main_window):
        """

        :param main_window:
        :return:
        """
        self._mainWindow = main_window

        return
