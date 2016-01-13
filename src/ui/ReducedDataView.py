########################################################################
#
# General-purposed plotting window
#
########################################################################
import sys
import numpy

from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import *

import GuiUtility


try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s
        
import gui.ui_GPView


class GeneralPurposedDataViewWindow(QMainWindow):
    """ Class for general-puposed plot window
    """
    # class
    def __init__(self, parent=None):
        """ Init
        """
        # call base
        QMainWindow.__init__(self)

        # Parent & others
        self._myParent = parent
        self._myController = None

        # current status
        self._currRunNumber = None
        self._currBank = 1
        self._currUnit = 'TOF'

        # set up UI
        self.ui = gui.ui_GPView.Ui_MainWindow()
        self.ui.setupUi(self)

        # Controlling data structure on lines that are plotted on graph
        self._linesDict = dict()  # key: tuple as run number and bank ID, value: line ID

        # Event handling
        # push buttons 
        self.connect(self.ui.pushButton_prevView, QtCore.SIGNAL('clicked()'),
                     self.doPlotRunPrev)
        self.connect(self.ui.pushButton_nextView, QtCore.SIGNAL('clicked()'),
                     self.doPlotRunNext)
        self.connect(self.ui.pushButton_plot, QtCore.SIGNAL('clicked()'),
                     self.doPlotRunSelected)

        # self.connect(self.ui.pushButton_allFillPlot, QtCore.SIGNAL('clicked()'),
        #         self.doPlotAllRuns)

        self.connect(self.ui.pushButton_normByCurrent, QtCore.SIGNAL('clicked()'),
                     self.do_normalise_by_current)

        self.connect(self.ui.pushButton_apply, QtCore.SIGNAL('clicked()'),
                     self.do_apply_new_range)

        # combo boxes
        self.connect(self.ui.comboBox_runs, QtCore.SIGNAL('currentIndexChanged(int)'),
                     self.evt_select_new_run_number)
        self.connect(self.ui.comboBox_spectraList, QtCore.SIGNAL('currentIndexChanged(int)'),
                     self.evt_bank_id_changed)
        self.connect(self.ui.comboBox_unit, QtCore.SIGNAL('currentIndexChanged(int'),
                     self.evt_unit_changed)

        return

    def do_apply_new_range(self):
        """ Apply new data range to the plots on graph
        Purpose: Change the X limits of the figure
        Requirements: min X and max X are valid float
        Guarantees: figure is re-plot
        :return: None
        """
        # Get new x range
        curr_min_x, curr_max_x = self.ui.graphicsView_mainPlot.getXLimits()
        new_min_x_str = str(self.ui.lineEdit_minX.text()).strip()
        if len(new_min_x_str) != 0:
            curr_min_x = float(new_min_x_str)

        new_max_x_str = str(self.ui.lineEdit_maxX.text()).strip()
        if len(new_max_x_str) != 0:
            curr_max_x = float(new_max_x_str)

        if curr_max_x <= curr_min_x:
            GuiUtility.pop_dialog_error(
                    'Minimum X %f is equal to or larger than maximum X %f!' % (curr_min_x, curr_max_x))
            return

        # Set new X range
        self.ui.graphicsView_mainPlot.setXLimits(curr_min_x, curr_max_x)

        return

    def do_normalise_by_current(self):
        """
        Normalize by current/proton charge if the reduced run is not.
        :return:
        """
        # Get run number
        run_number = int(self.ui.comboBox_runs.currentText())

        # Check
        if self._myController.get_reduced_run_history(run_number).is_noramalised_by_current() is True:
            GuiUtil.pop_error_message(self, 'Run %d has been normalised by current already.' % run_number)
            return

        # Normalize by current
        self._myController.normalise_by_current(run_number=run_number)

        # Re-plot
        bank_id = int(self.ui.comboBox_spectraList.currentText())
        over_plot = self.ui.checkBox_overPlot.isChecked()
        self.plot_run(run_number=run_number, bank_id=bank_id, over_plot=over_plot)

        return

    def doPlotRunSelected(self):
        """
        Plot the current run. The first choice is from the line edit. If it is blank,
        then from combo box
        :return:
        """
        # Get run numbers
        runs_str = str(self.ui.lineEdit_runs.text()).strip()
        if len(runs_str) > 0:
            run_numbers = self.parse_runs_list(runs_str)
        else:
            run_numbers = [int(self.ui.comboBox_runs.currentText())]

        over_plot = self.ui.checkBox_overPlot.isChecked()
        # TODO/FIXME/1st: replace the following by a method as get_bank_ids() for 'All' case
        bank_id = int(self.ui.comboBox_spectraList.currentText())
        for run_number in run_numbers:
            self.plot_run(run_number, bank_id, over_plot)

        return

    def doPlotRunNext(self):
        """
        Purpose: plot the previous run in the list and update the run list
        :return:
        """
        # Get previous index from combo box
        current_index = self.ui.comboBox_runs.currentIndex()
        current_index += 1
        # if the current index is at the beginning, then loop to the last run number
        if current_index == self.ui.comboBox_runs.count():
            current_index = 0
        elif current_index > self.ui.comboBox_runs.count():
            raise RuntimeError('It is impossible to have index larger than number of items.')

        # Get the current run
        self.ui.comboBox_runs.setCurrentIndex(current_index)
        run_number = int(self.ui.comboBox_runs.currentText())

        # Plot
        bank_id = int(self.ui.comboBox_spectraList.currentText())
        over_plot = self.ui.checkBox_overPlot.isChecked()
        self.plot_run(run_number, bank_id, over_plot)

        return

    def doPlotRunPrev(self):
        """
        Purpose: plot the previous run in the list and update the run list
        :return:
        """
        # Get previous index from combo box
        current_index = self.ui.comboBox_runs.currentIndex()
        current_index -= 1
        # if the current index is at the beginning, then loop to the last run number
        if current_index < 0:
            current_index = self.ui.comboBox_runs.count()-1

        # Get the current run
        self.ui.comboBox_runs.setCurrentIndex(current_index)
        run_number = int(self.ui.comboBox_runs.currentText())

        # Plot
        bank_id = int(self.ui.comboBox_spectraList.currentText())
        over_plot = self.ui.checkBox_overPlot.isChecked()
        self.plot_run(run_number, bank_id, over_plot)

        return

    def plot_run(self, run_number, bank_id, over_plot):
        """
        Plot a run on graph
        Requirements:
         1. run number is a positive integer
         2. bank id is a positive integer
        Guarantees:
        :param run_number:
        :param bank_id:
        :return:
        """
        # TODO/NOW/1st Review

        # Check requirements
        assert isinstance(run_number, int)
        assert run_number > 0
        assert isinstance(bank_id, int)
        assert bank_id > 0

        # Get data
        if run_number != self._currRunNumber:
            # get new data
            self._reducedDataDict = self._myController.get_reduced_data(run_number, self._currUnit)
            # update information
            self._currRunNumber = run_number

        # Get data from bank: convert bank to spectrum
        assert (bank_id-1) in self._reducedDataDict, 'bla bla'
        vec_x, vec_y = self._reducedDataDict[bank_id-1]
        self._currBank = bank_id

        # if previous image is not supposed to keep, then clear the holder
        if over_plot is False:
            self._linesDict = dict()

        # Plot the run
        label = "run %d bank %d" % (run_number, bank_id)
        line_id = self._plot(vec_x, vec_y, label=label, overplot=over_plot)
        self._linesDict[(run_number, bank_id)] = line_id

        # Change label
        self.ui.label_currentRun.setText(str(run_number))

        return

    def evt_bank_id_changed(self):
        """
        Handling the event that the bank ID is changed: the figure should be re-plot.
        It should be avoided to plot the same data twice against evt_select_new_run_number
        :return:
        """
        curr_bank_id = int(self.ui.comboBox_spectraList.currentText())
        keep_prev = self.ui.checkBox_overPlot.isChecked()
        self.plot_run(run_number=self._currRunNumber, bank_id=curr_bank_id, over_plot=keep_prev)

        return

    def evt_select_new_run_number(self):
        """ Event handling the case that a new run number is selected in combobox_run
        :return:
        """
        # Get the new run number
        run_number = int(self.ui.comboBox_runs.currentText())
        status, run_info = self._myController.get_reduced_run_info(run_number)
        if status is False:
            GuiUtility.pop_dialog_error(self, run_info)

        # Re-set the spectra list combo box
        bank_id_list = run_info
        self.ui.comboBox_spectraList.clear()
        for bank_id in bank_id_list:
            self.ui.comboBox_spectraList.addItems(str(bank_id))
        self.ui.comboBox_spectraList.addItem('All')

        return

    def evt_unit_changed(self):
        """
        Purpose: Re-plot the current plots with new unit
        :return:
        """
        # Check
        new_unit = str(self.ui.comboBox_unit.currentText())

        # Get the data sets and replace them with new unit
        for run_number in self._reducedDataDict.keys():
            self._reducedDataDict[run_number] = self._myController.get_reduced_data(run_number, new_unit)

        # Clear the line dictionary
        self._linesDict = dict()

        # Clear previous image and re-plot
        self.ui.graphicsView_mainPlot.remove_all_lines()
        for run_number in self._reducedDataDict.keys():
            self.plot_run(run_number, self._currBank, over_plot=True)

        # Reset current unit
        self._currUnit = new_unit

        return

    def setup(self, controller):
        """ Set up the GUI from controller
        :param controller:
        :return:
        """
        # Check
        # assert isinstance(controller, VDriveAPI)
        self._myController = controller

        # Set the reduced runs
        reduced_run_number_list = self._myController.get_reduced_runs()
        reduced_run_number_list.sort()
        self.ui.comboBox_runs.clear()
        for run_number in reduced_run_number_list:
            self.ui.comboBox_runs.addItem(str(run_number))

        return

    @staticmethod
    def parse_runs_list(run_list_str):
        """ Parse a list of runs in string such as 122, 133, 444, i.e., run numbers are separated by ,
        :param run_list_str:
        :return:
        """
        assert isinstance(run_list_str, str)

        items = run_list_str.strip().split(',')
        run_number_list = list()
        for item in items:
            item = item.strip()
            if item.isdigit():
                run_number = int(item)
                run_number_list.append(run_number)
        # END-FOR

        assert len(run_number_list) > 0, 'There is no valid run number in string %s.' % run_list_str

        return run_number_list


class MockParent:
    """ Mocking parent for universal purpose
    """
    def __init__(self):
        """ Init
        """
        # self._arrayX, self._arrayY, self._noteList = self._parseData()

        return


    def _parseData(self):
        datafile = open('./tests/mockdata.dat', 'r')
        rawlines = datafile.readlines()
        datafile.close()

        xlist = []
        ylist = []
        tlist = []

        for rline in rawlines:
            line = rline.strip()
            if len(line) == 0:
                continue

            terms = line.split()
            x = float(terms[0])
            y = float(terms[1])
            t = terms[0]

            xlist.append(x)
            ylist.append(y)
            tlist.append(t)

        x_array = numpy.array(xlist)
        y_array = numpy.array(ylist)

        return x_array, y_array, tlist

    # #--------------------------------------------------------------------
    # # For testing purpose
    # #--------------------------------------------------------------------
    # def computeMock(self):
    #     """ Compute vecx and vecy as mocking
    #     """
    #     import random, math

    #     x0 = 0.
    #     xf = 1.
    #     dx = 0.1

    #     vecx = []
    #     vecy = []

    #     x = x0
    #     while x < xf:
    #         y = 0.0
    #         vecx.append(x)
    #         vecy.append(y)
    #         x += dx

    #     xlim = [x0, xf]
    #     ylim = [-1., 1]

    #     return (vecx, vecy, xlim, ylim)



    # def getData(self, runnumber):
    #     """ Form two numpy array for plotting
    #     """
    #     return (self._arrayX, self._arrayY, self._noteList)

def testmain(argv):
    """ Main method for testing purpose
    """
    parent = MockParent()

    app = QtGui.QApplication(argv)

    # my plot window app
    myapp = GeneralPurposedDataViewWindow(parent)
    # myapp.setRuns(['002271'])
    myapp.show()

    exit_code=app.exec_()
    sys.exit(exit_code)


    return

if __name__ == "__main__":
    testmain(sys.argv)
