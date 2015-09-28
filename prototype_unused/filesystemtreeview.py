#
# An extension on QTreeView for file system
#

from PyQt4 import QtGui, QtCore
import os


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


