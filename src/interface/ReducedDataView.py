########################################################################
#
# General-purposed plotting window
#
########################################################################
import os
from PyQt4 import QtCore, QtGui

import gui.GuiUtility as GuiUtility

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s
        
import gui.ui_GPView
import vanadium_controller_dialog


class GeneralPurposedDataViewWindow(QtGui.QMainWindow):
    """ Class for general-purposed plot window to view reduced data
    """
    # class
    def __init__(self, parent=None):
        """ Init
        """
        # call base
        super(GeneralPurposedDataViewWindow, self).__init__(parent)

        # Parent & others
        self._myParent = parent
        self._myController = None

        self._bankIDList = ['1', '2', 'All']

        # Controlling data structure on lines that are plotted on graph
        self._reducedDataDict = dict()  # key: run number, value: dictionary (key = spectrum ID, value = (vec x, vec y)

        # current status
        self._iptsNumber = None
        self._runNumberList = None

        self._currRunNumber = None
        self._currBank = 1
        self._currUnit = 'TOF'

        self._choppedRunNumber = 0
        self._choppedSequenceList = None

        self._canvasDimension = 1
        self._plotType = None

        # mutexes to control the event handling for changes in widgets
        self._mutexRunNumberList = False
        self._mutexBankIDList = False

        # data structure to manage the fitting result
        self._stripBufferDict = dict()  # key = [self._iptsNumber, self._currRunNumber, self._currBank]
        self._vanStripPlotID = None
        self._smoothedPlotID = None

        # set up UI
        self.ui = gui.ui_GPView.Ui_MainWindow()
        self.ui.setupUi(self)

        # initialize widgets
        self._init_widgets()

        # Event handling
        # push buttons 
        self.connect(self.ui.pushButton_prevView, QtCore.SIGNAL('clicked()'),
                     self.do_plot_prev_run)
        self.connect(self.ui.pushButton_nextView, QtCore.SIGNAL('clicked()'),
                     self.do_plot_next_run)
        self.connect(self.ui.pushButton_plot, QtCore.SIGNAL('clicked()'),
                     self.doPlotRunSelected)

        # self.connect(self.ui.pushButton_allFillPlot, QtCore.SIGNAL('clicked()'),
        #         self.do_plot_all_runs)

        self.connect(self.ui.pushButton_normByCurrent, QtCore.SIGNAL('clicked()'),
                     self.do_normalise_by_current)

        self.connect(self.ui.pushButton_apply, QtCore.SIGNAL('clicked()'),
                     self.do_apply_new_range)

        self.connect(self.ui.pushButton_cancel, QtCore.SIGNAL('clicked()'),
                     self.do_close)

        # combo boxes
        self.connect(self.ui.comboBox_runs, QtCore.SIGNAL('currentIndexChanged(int)'),
                     self.evt_select_new_run_number)
        self.connect(self.ui.comboBox_spectraList, QtCore.SIGNAL('currentIndexChanged(int)'),
                     self.evt_bank_id_changed)
        self.connect(self.ui.comboBox_unit, QtCore.SIGNAL('currentIndexChanged(int)'),
                     self.evt_unit_changed)

        # vanadium
        self.connect(self.ui.pushButton_launchVanProcessDialog, QtCore.SIGNAL('clicked()'),
                     self.do_launch_vanadium_dialog)

        # sub window
        self._vanadiumProcessDialog = None

        return

    def _init_widgets(self):
        """
        Initialize some widgets
        :return:
        """
        # bank list
        self.ui.comboBox_spectraList.addItem('1')
        self.ui.comboBox_spectraList.addItem('2')
        self.ui.comboBox_spectraList.addItem('All')

    def add_data_set(self, controller_data_key):
        """
        add a new data set to this data viewer window
        :param controller_data_key:
        :return:
        """
        # return if the controller data key exist
        if controller_data_key in self._reducedDataDict:
            return

        # show on the list: turn or and off mutex locks around change of the combo box contents
        self._mutexRunNumberList = True
        # clear existing runs
        self.ui.comboBox_runs.addItem(str(controller_data_key))
        # release mutex lock
        self._mutexRunNumberList = False

        # get reduced data set from controller
        status, ret_obj = self._myController.get_reduced_data(controller_data_key,
                                                              target_unit=self._currUnit)
        # return if unable to get reduced data
        if status is False:
            raise RuntimeError('Unable to load data by key {0} due to {1}.'.format(controller_data_key,
                                                                                   ret_obj))
        # add data set (arrays)
        reduced_data_dict = ret_obj
        assert isinstance(reduced_data_dict, dict), 'Reduced data set should be dict but not %s.' \
                                                    '' % type(reduced_data_dict)

        # add the returned data objects to dictionary
        self._reducedDataDict[controller_data_key] = reduced_data_dict

        return controller_data_key

    def add_run_numbers(self, run_number_list, clear_previous=False):
        """
        set run numbers to combo-box-run numbers
        :param run_number_list:
        :return:
        """
        assert isinstance(run_number_list, list), 'Input %s must be a list of run numbers but not of type %s.' \
                                                  '' % (str(run_number_list), type(run_number_list))

        self._runNumberList = run_number_list[:]
        self._runNumberList.sort()

        # show on the list: turn or and off mutex locks around change of the combo box conents
        self._mutexRunNumberList = True

        # clear existing runs
        if clear_previous:
            self.ui.comboBox_runs.clear()
        for run_number in self._runNumberList:
            self.ui.comboBox_runs.addItem(str(run_number))

        # release mutex lock
        self._mutexRunNumberList = False

        return

    def do_apply_new_range(self):
        """ Apply new data range to the plots on graph
        Purpose: Change the X limits of the figure
        Requirements: min X and max X are valid float
        Guarantees: figure is re-plot
        :return: None
        """
        # Get new x range
        curr_min_x, curr_max_x = self.ui.graphicsView_mainPlot.getXLimit()
        new_min_x_str = str(self.ui.lineEdit_minX.text()).strip()
        if len(new_min_x_str) != 0:
            curr_min_x = float(new_min_x_str)

        new_max_x_str = str(self.ui.lineEdit_maxX.text()).strip()
        if len(new_max_x_str) != 0:
            curr_max_x = float(new_max_x_str)

        if curr_max_x <= curr_min_x:
            GuiUtility.pop_dialog_error(self, 'Minimum X %f is equal to or larger than maximum X %f!'
                                              '' % (curr_min_x, curr_max_x))
            return

        # Set new X range
        self.ui.graphicsView_mainPlot.setXYLimit(xmin=curr_min_x, xmax=curr_max_x)

        return

    def do_close(self):
        """ Close the window
        :return:
        """
        self.close()

    def do_normalise_by_current(self):
        """
        Normalize by current/proton charge if the reduced run is not.
        :return:
        """
        # Get run number
        run_number = int(self.ui.comboBox_runs.currentText())

        # Get reduction information from run number
        status, ret_obj = self._myController.get_reduced_run_info(run_number)
        assert status, ret_obj
        reduction_info = ret_obj

        if reduction_info.is_noramalised_by_current() is True:
            GuiUtility.pop_dialog_error(self, 'Run %d has been normalised by current already.' % run_number)
            return

        # Normalize by current
        self._myController.normalise_by_current(run_number=run_number)

        # Re-plot
        bank_id = int(self.ui.comboBox_spectraList.currentText())
        over_plot = self.ui.checkBox_overPlot.isChecked()
        self.plot_run(run_number=run_number, bank_id=bank_id, over_plot=over_plot)

        return

    def do_launch_vanadium_dialog(self):
        """
        launch the vanadium run processing dialog
        :return:
        """
        self._vanadiumProcessDialog = vanadium_controller_dialog.VanadiumProcessControlDialog(self)
        self._vanadiumProcessDialog.show()

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

    def do_plot_next_run(self):
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

    def do_plot_prev_run(self):
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

    def evt_bank_id_changed(self):
        """
        Handling the event that the bank ID is changed: the figure should be re-plot.
        It should be avoided to plot the same data twice against evt_select_new_run_number
        :return:
        """
        # skip if it is locked
        if self._mutexBankIDList:
            return

        # Get new bank ID
        new_bank_str = str(self.ui.comboBox_spectraList.currentText()).strip()
        if new_bank_str.isdigit() is False:
            print '[DB] New bank ID %s is not an allowed integer.' % new_bank_str
            return

        curr_bank_id = int(new_bank_str)
        keep_prev = self.ui.checkBox_overPlot.isChecked()
        if self._currRunNumber is not None:
            self.plot_run(run_number=self._currRunNumber, bank_id=curr_bank_id, over_plot=keep_prev)

        return

    def evt_select_new_run_number(self):
        """ Event handling the case that a new run number is selected in combobox_run
        :return:
        """
        # skip if it is locked
        if self._mutexRunNumberList:
            return

        # Get the new run number
        run_number = str(self.ui.comboBox_runs.currentText())
        try:
            run_number = int(run_number)
            status, run_info = self._myController.get_reduced_run_info(run_number)
            bank_id_list = run_info
        except ValueError as value_err:
            raise NotImplementedError('Unable to get run information from run {0} due to {1}'.format(run_number, value_err))
        self._currRunNumber = run_number

        if status is False:
            GuiUtility.pop_dialog_error(self, run_info)

        # Re-set the spectra list combo box

        if len(bank_id_list) != len(self._bankIDList) - 1:
            # different number of banks
            self.ui.comboBox_spectraList.clear()
            for bank_id in bank_id_list:
                self.ui.comboBox_spectraList.addItem(str(bank_id))
            self.ui.comboBox_spectraList.addItem('All')

            # reset current bank ID list
            self._bankIDList = bank_id_list[:]
            self._bankIDList.append('All')

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
            status, ret_obj = self._myController.get_reduced_data(run_number, new_unit)
            if status is False:
                GuiUtility.pop_dialog_error(self, 'Unable to get run %d with new unit %s due to %s.' % (
                    run_number, new_unit, ret_obj
                ))
                return
            self._reducedDataDict[run_number] = ret_obj
        # END-FOR

        # Reset current unit
        self._currUnit = new_unit

        # Clear previous image and re-plot
        self.ui.graphicsView_mainPlot.clear_all_lines()
        for run_number in self._reducedDataDict.keys():
            self.plot_run(run_number, self._currBank, over_plot=True)

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

        # check validity
        assert len(run_number_list) > 0, 'There is no valid run number in string %s.' % run_list_str

        return run_number_list

    def plot_chopped_run(self, bank_id=1, bank_id_from_1=True, chopped_data_dir=None):
        """
        Plot a chopped run
        :param bank_id:
        :param bank_id_from_1:
        :param chopped_data_dir: diectory of chopped data
        :return:
        """
        assert self._choppedRunNumber > 0, 'The chopped run number %s must be a positive integer. If None, very ' \
                                           'likely not specified yet.' % str(self._choppedRunNumber)
        assert isinstance(self._choppedSequenceList, list), 'Chopped sequence list %s must be a LIST.' \
                                                            '' % str(self._choppedSequenceList)

        # directory to search data
        if chopped_data_dir is not None:
            dirs_to_search = [chopped_data_dir]
        else:
            # default
            dirs_to_search = os.path.abspath('.')

        if len(self._choppedSequenceList) == 1:
            # 1D plot
            status, ret_obj = self._myController.get_reduced_chopped_data(self._iptsNumber, self._choppedRunNumber,
                                                                          self._choppedSequenceList[0],
                                                                          search_archive=True,
                                                                          search_dirs=dirs_to_search)
            if not status:
                GuiUtility.pop_dialog_error(self, ret_obj)
                return
            else:
                # FIXME/TODO/ISSUE/55+ Make it robust
                assert isinstance(ret_obj, dict), 'Returned object from get_reduced_chopped_data() must be a ' \
                                                  'dictionary but not a {0}.'.format(type(ret_obj))
                bank_data = ret_obj[bank_id-1]
                vec_x = bank_data[0]
                vec_y = bank_data[1]

            title = 'Chopped run {0} sequence {1}.'.format(self._choppedRunNumber, self._choppedSequenceList[0])
            self.ui.graphicsView_mainPlot.add_plot_1d(vec_x, vec_y, x_label='TOF', label=title)

        else:
            # 2D plot
            error_message = ''
            chop_seq_list = list()
            data_set_list = list()

            for seq_number in self._choppedSequenceList:
                # get reduced GSAS data
                # ipts_number, run_number, chop_seq, search_archive=True, search_dirs=None)
                status, ret_obj = self._myController.get_reduced_chopped_data(self._iptsNumber, self._choppedRunNumber,
                                                                              seq_number, search_archive=True,
                                                                              search_dirs=dirs_to_search)
                if not status:
                    error_message += 'Unable to retrieve run %d chopped section %d due to %s.\n' \
                                     '' % (self._choppedRunNumber, seq_number, ret_obj)
                    continue

                data_set_dict = ret_obj
                assert isinstance(data_set_dict, dict), 'data set dictionary %s must be a dictionary.' \
                                                        '' % str(data_set_dict)
                if bank_id_from_1:
                    spec_id = bank_id - 1
                else:
                    spec_id = bank_id
                assert spec_id in data_set_dict, 'Spectrum ID %d must be in data set dictionary with keys %s.' \
                                                 '' % (spec_id, str(data_set_dict.keys()))

                chop_seq_list.append(seq_number)

                vec_x = data_set_dict[spec_id][0]
                vec_y = data_set_dict[spec_id][1]
                data_set_list.append((vec_x, vec_y))
                print data_set_list[-1]
            # END-FOR

            if len(chop_seq_list) == 0:
                GuiUtility.pop_dialog_error(self, error_message)
                return

            self.ui.graphicsView_mainPlot.plot_2d_contour(chop_seq_list, data_set_list)

            if len(error_message) > 0:
                GuiUtility.pop_dialog_error(self, error_message)

        # END-IF-ELSE

        return

    def plot_multiple_runs(self, bank_id, bank_id_from_1=False):
        """
        Plot multiple runs (reduced data) to contour plot.
        :return:
        """
        assert isinstance(bank_id, int) and bank_id >= 0, 'Bank ID %s must be a non-negetive integer.' \
                                                          '' % str(bank_id)

        # get the list of runs
        error_msg = ''
        run_number_list = list()
        data_set_list = list()

        for run_number in self._runNumberList:
            status, ret_obj = self.get_reduced_data(run_number, bank_id, bank_id_from_1=bank_id_from_1)
            if status:
                run_number_list.append(run_number)
                data_set_list.append(ret_obj)
            else:
                error_msg += 'Unable to get reduced data for run %d due to %s;\n' % (run_number, str(ret_obj))
                continue
        # END-FOR

        # return if nothing to plot
        if len(run_number_list) == 0:
            GuiUtility.pop_dialog_error(self, error_msg)
            return

        # plot
        self.ui.graphicsView_mainPlot.plot_2d_contour(run_number_list, data_set_list)

        if len(error_msg) > 0:
            GuiUtility.pop_dialog_error(self, error_msg)

        return

    def get_reduced_data(self, run_number, bank_id, bank_id_from_1=True):
        """
        get reduced data in vectors of X and Y
        :param run_number: data key or run number
        :param bank_id:
        :param bank_id_from_1:
        :return: 2-tuple [1] True, (vec_x, vec_y); [2] False, error_message
        """
        # Get data (run)
        if run_number not in self._reducedDataDict:
            # get new data
            status, ret_obj = self._myController.get_reduced_data(run_number, self._currUnit,
                                                                  ipts_number=self._iptsNumber,
                                                                  search_archive=True)

            # return if unable to get reduced data
            if status is False:
                return status, str(ret_obj)

            # check returned data dictionary and set
            reduced_data_dict = ret_obj
            assert isinstance(reduced_data_dict, dict), 'Reduced data set should be dict but not %s.' \
                                                        '' % type(reduced_data_dict)

            # add the returned data objects to dictionary
            self._reducedDataDict[run_number] = reduced_data_dict
        else:
            # previously obtained and stored
            reduced_data_dict = self._reducedDataDict[run_number]
        # END-IF

        # Get data from bank: convert bank to spectrum
        bank_id_list = reduced_data_dict.keys()
        if 0 in bank_id_list:
            spec_id_from_0 = True
        else:
            spec_id_from_0 = False

        # determine the spectrum ID from controller
        if bank_id_from_1 and spec_id_from_0:
            spec_id = bank_id - 1
        else:
            spec_id = bank_id

        # check again
        if spec_id not in reduced_data_dict:
            raise RuntimeError('Bank ID %d (spec ID %d) does not exist in reduced data dictionary with spectra '
                               '%s.' % (bank_id, spec_id, str(reduced_data_dict.keys())))

        vec_x = self._reducedDataDict[run_number][spec_id][0]
        vec_y = self._reducedDataDict[run_number][spec_id][1]

        return True, (vec_x, vec_y)

    def plot_data(self, data_key, bank_id, clear_previous=False, is_workspace_name=False):
        """
        plot a spectrum in a workspace
        :param data_key: key to find the workspace or the workspace name
        :param bank_id:
        :param clear_previous: flag to clear the plots on the current canvas
        :param is_workspace_name: flag to indicate that the given data_key is a workspace's name
        :return:
        """
        # clear canvas
        if clear_previous:
            # clear canvas and set X limit to 0. and 1.
            self.ui.graphicsView_mainPlot.reset_1d_plots()

        # check inputs
        if is_workspace_name:
            # the given data_key is a workspace's name, then get the vector X and vector Y from mantid workspace
            status, ret_obj = self._myController.get_data_from_workspace(data_key, bank_id=self._currBank,
                                                                         target_unit=None,
                                                                         starting_bank_id=1)
            if not status:
                err_msg = str(ret_obj)
                GuiUtility.pop_dialog_error(self, err_msg)
                return

            data_set = ret_obj[0][bank_id]
            vec_x = data_set[0]
            vec_y = data_set[1]

            current_unit = ret_obj[1]

            label = 'Vanadium Peak Stripped'
        else:
            if data_key not in self._reducedDataDict:
                raise RuntimeError('Viewer data key {0} is not a key in "ReducedDataDictionary".'.format(data_key))

            # get data
            vec_x = self._reducedDataDict[data_key][bank_id][0]
            vec_y = self._reducedDataDict[data_key][bank_id][1]

            label = "Run {0} bank {1}".format(data_key, bank_id)

            current_unit = self._currUnit
        # END-IF-ELSE

        # plot
        line_id = self.ui.graphicsView_mainPlot.plot_1d_data(vec_x, vec_y, x_unit=current_unit, label=label,
                                                             line_key=data_key)

        self.ui.graphicsView_mainPlot.auto_rescale()

        return line_id

    def plot_run(self, run_number, bank_id, over_plot=False):
        """
        Plot a run on graph
        Requirements:
         1. run number is a positive integer
         2. bank id is a positive integer
        Guarantees:
        :param run_number:
        :param bank_id:
        :param over_plot:
        :return:
        """
        # Check requirements
        assert isinstance(run_number, int), 'Run number %s must be an integer but not %s.' % (str(run_number),
                                                                                              str(type(run_number)))
        assert run_number > 0
        assert isinstance(bank_id, int), 'Bank ID %s must be an integer, but not %s.' % (str(bank_id),
                                                                                         str(type(bank_id)))
        assert bank_id > 0, 'Bank ID %d must be positive.' % bank_id

        # Get data (run)
        status, ret_obj = self.get_reduced_data(run_number, bank_id)
        if status:
            vec_x, vec_y = ret_obj
        else:
            GuiUtility.pop_dialog_error(self, ret_obj)
            return

        # update information
        self._currRunNumber = run_number
        self._currBank = bank_id

        # Plot the run
        # TODO/FIXME/ISSUE/59: Move the plotting part to extended graphics view class
        label = "run %d bank %d" % (run_number, bank_id)
        if over_plot is False:
            self.ui.graphicsView_mainPlot.clear_all_lines()
        line_id = self.ui.graphicsView_mainPlot.add_plot_1d(vec_x=vec_x, vec_y=vec_y, label=label,
                                                            x_label=self._currUnit, marker='.', color='red')
        # self._linesDict[(run_number, bank_id)] = line_id

        # Change label
        self.ui.label_currentRun.setText(str(run_number))

        # And resize the image if it is necessary
        self.resize_canvas()

        # set combo box value correct
        self._mutexBankIDList = True
        combo_index = self._bankIDList.index(str(bank_id))
        self.ui.comboBox_spectraList.setCurrentIndex(combo_index)
        self._mutexBankIDList = False

        self.ui.label_currentRun.setText('Run %d' % run_number)

        return

    def resize_canvas(self):
        """
        Resize the canvas if it is necessary
        :return:
        """
        # Init
        min_x = 1.E20
        max_x = -1.E20

        # Find minimum x and maximum x
        for run_number in self._reducedDataDict.keys():
            run_data_dict = self._reducedDataDict[run_number]
            assert isinstance(run_data_dict, dict)
            for spec_id in run_data_dict.keys():
                vec_x = run_data_dict[spec_id][0]
                min_x = min(min_x, vec_x[0])
                max_x = max(max_x, vec_x[-1])
        # END-FOR

        # Resize the canvas
        self.ui.graphicsView_mainPlot.setXYLimit(xmin=min_x, xmax=max_x)

        return

    def set_canvas_type(self, dimension, multi_dim_type=None):
        """
        set the canvas type: 1D, 2D, 3D, fill plot or etc
        :param dimension:
        :param multi_dim_type: type for multiple dimension plot
        :return:
        """
        # check
        assert isinstance(dimension, int), 'Dimension must be an integer but not %s.' % type(dimension)
        assert multi_dim_type is None or isinstance(multi_dim_type, str), 'Multiple-dimension plot type ' \
                                                                          'must be None or string but not ' \
                                                                          '%s.' % type(multi_dim_type)

        # change canvas/plot type?
        change_canvas_type = False
        if self._canvasDimension != dimension:
            change_canvas_type = True
        elif multi_dim_type is not None and self._plotType != multi_dim_type:
            change_canvas_type = True

        # set canvas
        if change_canvas_type:
            target_dim = dimension
            if multi_dim_type is not None:
                target_type = multi_dim_type
            else:
                target_type = self._plotType
            self.ui.graphicsView_mainPlot.set_dimension_type(target_dim, target_type)

            self._canvasDimension = dimension
            self._plotType = multi_dim_type
        # END-IF

        return

    def set_chop_run_number(self, run_number):
        """
        set chopped run number to view chopped data in 2D mode
        :param run_number:
        :return:
        """
        assert isinstance(run_number, int) and run_number > 0, 'run number %s must be a positive integer.' \
                                                               '' % str(run_number)

        self._choppedRunNumber = run_number

        return

    def set_chop_sequence(self, chop_run_sequence_list):
        """
        set a sequence of integers to self._choppedSequenceList
        :param chop_run_sequence_list:
        :return:
        """
        assert isinstance(chop_run_sequence_list, list), 'Input chopped run sequence must be a list.'
        for seq in chop_run_sequence_list:
            assert isinstance(seq, int) and seq >= 0, 'Sequence %s in list must be a non-negative integer.' \
                                                      '' % str(seq)

        self._choppedSequenceList = chop_run_sequence_list[:]

        return

    def set_ipts_number(self, ipts_number):
        """

        :param ipts_number:
        :return:
        """
        assert isinstance(ipts_number, int), 'Set IPTS number must be an integer.'

        self._iptsNumber = ipts_number

        return

    def set_title(self, title):
        """
        blalba
        :param title:
        :return:
        """
        self.ui.label_currentRun.setText(title)

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

    # FIXME/TODO/ISSUE/59: Starting to implementing all methods below!!!

    def signal_strip_vanadium_peaks(self, peak_fwhm, tolerance, background_type, is_high_background):
        """
        process the signal to strip vanadium peaks
        :param peak_fwhm:
        :param tolerance:
        :param background_type:
        :param is_high_background:
        :return:
        """
        print '[DB...BAT] Striping vanadium peak of current run {0} with {1}, {2}, {3}, {4}.' \
              ''.format(self._currRunNumber, peak_fwhm, tolerance, background_type, is_high_background)

        # note: as it is from a signal with defined parameters types, there is no need to check
        #       the validity of parameters

        # strip vanadium peaks
        if self._currRunNumber is None:
            data_key = str(self.ui.comboBox_runs.currentText())
        else:
            data_key = None

        status, ret_obj = self._myController.strip_vanadium_peaks(self._iptsNumber, self._currRunNumber,
                                                                  self._currBank, peak_fwhm, tolerance,
                                                                  background_type, is_high_background,
                                                                  data_key)
        if status:
            result_ws_name = ret_obj
        else:
            err_msg = ret_obj
            GuiUtility.pop_dialog_error(self, err_msg)
            return

        # plot the data without vanadium peaks
        #
        self._vanStripPlotID = self.plot_data(data_key=result_ws_name, bank_id=self._currBank,
                                              clear_previous=True, is_workspace_name=True)

        print '[HOW TO RECORD?] ', self._iptsNumber, self._currBank, self._currBank

        self._stripBufferDict[self._iptsNumber, self._currRunNumber, self._currBank] = result_ws_name

        return

    def signal_smooth_vanadium(self, smoother_type, param_n, param_order):
        """
        process the signal to smooth vanadium spectra
        :param smoother_type:
        :param param_n:
        :param param_order:
        :return:
        """
        print '[DB...BAT] Smoothing vanadium run {0} bank {1} with smoother of type {2} and parameter {3}, {4}.' \
              ''.format(self._currRunNumber, self._currBank, smoother_type, param_n, param_order)

        # call the original data to for smoothing
        print '[DB...BAT] Record: ', self._stripBufferDict


        status, ret_obj = self._myController.smooth_data(self._iptsNumber, self._currRunNumber, self._currBank,
                                                         smoother_type, param_n, param_order)
        if status:
            result_data_key = ret_obj
            self._smoothBufferDict[self._iptsNumber, self._currRunNumber, self._currBank] = result_data_key
        else:
            err_msg = ret_obj
            GuiUtility.pop_dialog_error(self, 'Unable to smooth data due to {0}.'.format(err_msg))

        # plot data
        self.ui.graphicsView_mainPlot.reset()
        self.plot_data(data_key=result_data_key, bank_id=self._currBank)

        return

    def signal_undo_strip_van_peaks(self):
        """
        undo the strip vanadium peak action, i.e., delete the previous result and remove the plot
        :return:
        """
        print '[DB...BAT] Undo Peak Striping.'

        if self._vanStripPlotID is None:
            print '[INFO] There is no vanadium-peak-removed spectrum to remove from canvas.'
            return

        # remove the plot
        self.ui.graphicsView_mainPlot.remove_line(line_id=self._vanStripPlotID)
        self._vanStripPlotID = None

        return

    def signal_undo_smooth_vanadium(self):
        """
        undo the smoothing operation on the spectrum including
        1. delete the result
        2. remove the smoothed plot
        :return:
        """
        print '[DB...BAT] Undo Peak Smoothing.'

        # return if there is no such action before
        if self._smoothedPlotID is None:
            print '[INFO] There is no smoothed spectrum to undo.'
            return

        # remove the plot
        self.ui.graphicsView_mainPlot.remove_line(self._vanStripPlotID)
        self._smoothedPlotID = None

        return