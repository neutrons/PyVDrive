########################################################################
#
# Window for set up log slicing splitters
#
########################################################################
import sys
import numpy
from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

import GuiUtility
import gui.VdriveLogPicker as VdriveLogPicker


OUT_PICKER = 0
IN_PICKER = 1
IN_PICKER_MOVING = 2
IN_PICKER_SELECTION = 3


class WindowLogPicker(QtGui.QMainWindow):
    """ Class for general-puposed plot window
    """
    # class
    def __init__(self, parent=None, init_run=None):
        """ Init
        """
        # call base
        QtGui.QMainWindow.__init__(self)

        # parent
        self._myParent = parent

        # set up UI
        self.ui = VdriveLogPicker.Ui_MainWindow()
        self.ui.setupUi(self)

        # Defining widget handling methods
        self.connect(self.ui.pushButton_selectIPTS, QtCore.SIGNAL('clicked()'),
                     self.do_select_ipts)
        self.connect(self.ui.pushButton_cancel, QtCore.SIGNAL('clicked()'),
                     self.do_quit_no_save)
        self.connect(self.ui.pushButton_saveReturn, QtCore.SIGNAL('clicked()'),
                     self.do_quit_with_save)
        self.connect(self.ui.pushButton_loadRunSampleLog, QtCore.SIGNAL('clicked()'),
                     self.do_load_run)
        self.connect(self.ui.pushButton_prevLog, QtCore.SIGNAL('clicked()'),
                     self.do_load_prev_log)
        self.connect(self.ui.pushButton_nextLog, QtCore.SIGNAL('clicked()'),
                     self.do_load_next_log)
        self.connect(self.ui.pushButton_readLogFile, QtCore.SIGNAL('clicked()'),
                     self.do_read_log_file)

        self.connect(self.ui.radioButton_useGenericDAQ, QtCore.SIGNAL('toggled()'),
                     self.do_set_log_options)
        self.connect(self.ui.radioButton_useLoadFrame, QtCore.SIGNAL('toggled()'),
                     self.do_set_log_options)
        self.connect(self.ui.radioButton_useLogFile, QtCore.SIGNAL('toggled()'),
                     self.do_set_log_options)

        # Add slicer picker
        self.connect(self.ui.pushButton_addPicker, QtCore.SIGNAL('clicked()'),
                     self.do_picker_add)
        self.connect(self.ui.pushButton_abortPicker, QtCore.SIGNAL('clicked()'),
                     self.do_picker_abort)
        self.connect(self.ui.pushButton_setPicker, QtCore.SIGNAL('clicked()'),
                     self.do_picker_set)
        self.connect(self.ui.pushButton_selectPicker, QtCore.SIGNAL('clicked()'),
                     self.do_enter_select_picker_mode)
        self.connect(self.ui.pushButton_processPickers, QtCore.SIGNAL('clicked()'),
                     self.do_picker_process)

        # Slicer table
        self.connect(self.ui.pushButton_selectAll, QtCore.SIGNAL('clicked()'),
                     self.do_select_time_segments)
        self.connect(self.ui.pushButton_deselectAll, QtCore.SIGNAL('clicked()'),
                     self.do_deselect_time_segments)

        # Further operation
        self.connect(self.ui.pushButton_highlight, QtCore.SIGNAL('clicked()'),
                     self.do_highlite_selected)
        self.connect(self.ui.pushButton_processSegments, QtCore.SIGNAL('clicked()'),
                     self.do_slice_segments)

        # Canvas
        self.connect(self.ui.pushButton_resizeCanvas, QtCore.SIGNAL('clicked()'),
                     self.do_resize_canvas)

        self.connect(self.ui.comboBox_logNames, QtCore.SIGNAL('currentIndexChanged(int)'),
                     self.evt_plot_sample_log)

        # Event handling for pickers
        self.ui.graphicsView_main._myCanvas.mpl_connect('button_press_event',
                                                        self.on_mouse_press_event)
        self.ui.graphicsView_main._myCanvas.mpl_connect('button_release_event',
                                                        self.on_mouse_release_event)
        self.ui.graphicsView_main._myCanvas.mpl_connect('motion_notify_event',
                                                        self.on_mouse_motion)

        # Initial setup
        self.ui.radioButton_useGenericDAQ.setChecked(True)
        self.ui.radioButton_useLoadFrame.setChecked(False)
        self.ui.radioButton_useLogFile.setChecked(False)
        if init_run is not None:
            assert isinstance(init_run, int)
            self.ui.lineEdit_runNumber.setText('%d' % init_run)

        # Class variables
        self._currentLogIndex = 0
        self._logNameList = list()

        self._currentPickerID = None
        self._myPickerMode = OUT_PICKER
        self._currMousePosX = 0.
        self._currMousePosY = 0.

        # Picker management
        self._myPickerIDList = list()

        # Set up widgets
        self._init_widgets_setup()

        return

    def _init_widgets_setup(self):
        """

        :return:
        """
        self.ui.tableWidget_segments.setup()

        self.ui.treeView_iptsRun.set_main_window(self)

    def do_select_time_segments(self):
        """

        :return:
        """
        # TODO/FIXME/NOW: select all time segments in table

    def do_deselect_time_segments(self):
        """

        :return:
        """
        # TODO/FIXME/NOW: deselect all time segments in table

    def do_highlite_selected(self):
        """

        :return:
        """
        # TODO/FIXME/NOW: high light (by different color) the selected time segments

    def do_slice_segments(self):
        """

        :return:
        """
        # TODO/FIXME/NOW: generate 2nd level event filters
        # Run GenerateEventFilters

    def do_load_run(self):
        """

        :return:
        """
        # Get run number
        run_number = GuiUtility.parse_integer(self.ui.lineEdit_runNumber)
        if run_number is None:
            GuiUtility.pop_dialog_error('Unable to load run as value is not specified.')

        # Get sample logs
        try:
            sample_log_names = self._myParent.load_sample_run(run_number, True)
        except RuntimeError as err:
            GuiUtility.pop_dialog_error('Unable to load sample logs from run %d due to %s.' % (run_number, str(err)))
            return

        # Set up
        self.ui.comboBox_logNames.clear()
        for log_name in sorted(sample_log_names):
            # self.ui.comboBox_logNames.addItem(QtCore.QString(log_name))
            self.ui.comboBox_logNames.addItem(str(log_name))
        self._currentLogIndex = 0
        self._logNameList = sample_log_names[:]

        # Set
        log_name = str(self.ui.comboBox_logNames.currentText())
        log_name = log_name.replace(' ', '').split('(')[0]
        self.plot_sample_log(log_name)

        return

    def do_enter_select_picker_mode(self):
        """ Enter picker selection mode
        :return:
        """
        if self._myPickerMode == IN_PICKER_MOVING:
            GuiUtility.pop_dialog_error(self, 'Canvas is in log-picker moving mode.  '
                                              'It is not allowed to enter picker-selection mode.')
            return

        self._myPickerMode = IN_PICKER_SELECTION

        return

    def do_load_next_log(self):
        """ Load next log
        :return:
        """
        # Next index
        next_index = self._currentLogIndex + 1
        if next_index > len(self._logNameList):
            next_index = 0
        sample_log_name = self._logNameList[next_index]

        # Plot
        self.plot_sample_log(sample_log_name)

        # Change status if plotting is successful
        self._currentLogIndex = next_index
        self.ui.comboBox_logNames.setCurrentIndex(self._currentLogIndex)

        return

    def do_load_prev_log(self):
        """ Load previous log
        :return:
        """
        # Previous index
        prev_index = self._currentLogIndex - 1
        if prev_index < 0:
            prev_index = len(self._logNameList) - 1
        sample_log_name = self._logNameList[prev_index]

        # Plot
        self.plot_sample_log(sample_log_name)

        # Change combobox index
        self._currentLogIndex = prev_index
        self.ui.comboBox_logNames.setCurrentIndex(self._currentLogIndex)

        return

    def do_quit_no_save(self):
        """
        Cancelled
        :return:
        """
        self.close()

        return

    def do_picker_abort(self):
        """
        Abort the action to add a picker
        :return:
        """
        # Guide user from enable/disable widgets
        self.ui.pushButton_addPicker.setEnabled(True)
        self.ui.pushButton_setPicker.setDisabled(True)
        self.ui.pushButton_abortPicker.setDisabled(True)
        self.ui.pushButton_selectPicker.setEnabled(True)

        # Delete the current picker
        self.ui.graphicsView_main.remove_indicator(self._currentPickerID)
        self._myPickerIDList.pop(self._currentPickerID)
        self._currentPickerID = None

        self._myPickerMode = OUT_PICKER

        return

    def do_picker_add(self):
        """
        Add picker
        :return:
        """
        # Add a picker
        indicator_id = self.ui.graphicsView_main.add_vertical_indicator(color='red')

        # Guide user
        self.ui.pushButton_setPicker.setEnabled(True)
        self.ui.pushButton_abortPicker.setEnabled(True)
        self.ui.pushButton_addPicker.setDisabled(True)
        self.ui.pushButton_deletePicker.setDisabled(True)
        self.ui.pushButton_selectPicker.setDisabled(True)

        # Change status
        self._currentPickerID = indicator_id
        self._myPickerMode = IN_PICKER
        self._myPickerIDList.append(indicator_id)

        return

    def do_picker_process(self):
        """
        Process pickers by sorting and fill the stop time
        :return:
        """
        self.ui.tableWidget_segments.select_time_segments(value=False)
        self.ui.tableWidget_segments.sort_by_start()
        self.ui.tableWidget_segments.sort_by_start_time()

        return

    def do_picker_set(self):
        """
        Add the (open) picker to list
        :return:
        """
        # Fix the current picker
        x, x = self.ui.graphicsView_main.get_indicator_position(self._currentPickerID)
        current_time = x
        print 'TODO Add picked up time %.5f' % current_time

        # Change the color
        self.ui.graphicsView_main.update_indicator(self._currentPickerID, color='black')

        # Guide user
        self.ui.pushButton_abortPicker.setDisabled(True)
        self.ui.pushButton_addPicker.setEnabled(True)
        self.ui.pushButton_deletePicker.setEnabled(True)
        self.ui.pushButton_setPicker.setDisabled(True)
        self.ui.pushButton_selectPicker.setEnabled(True)

        # Change status
        self._myPickerMode = OUT_PICKER
        self._currentPickerID = None

        # Set to table
        self.ui.tableWidget_segments.append_start_time(current_time)

        return

    def do_quit_with_save(self):
        """ Save selected segment and quit
        :return:
        """
        # Get splitters
        split_tup_list = self.get_splitters()

        # Close
        self.close()

        # Call parent method
        if self._myParent is not None:
            # FIXME/TODO/NOW - no method named set_splitter_info
            self._myParent.set_splitter_info(self._currRun, split_tup_list)

        return

    def do_read_log_file(self):
        """

        :return:
        """
        # TODO

    def do_resize_canvas(self):
        """ Resize canvas
        :return:
        """
        # Current setup
        curr_min_x, curr_max_x = self.ui.graphicsView_main.getXLimit()
        curr_min_y, curr_max_y = self.ui.graphicsView_main.getYLimit()

        # Future setup
        new_min_x = GuiUtility.parse_float(self.ui.lineEdit_minX)
        if new_min_x is None:
            new_min_x = curr_min_x

        new_max_x = GuiUtility.parse_float(self.ui.lineEdit_maxX)
        if new_max_x is None:
            new_max_x = curr_max_x

        new_min_y = GuiUtility.parse_float(self.ui.lineEdit_minY)
        if new_min_y is None:
            new_min_y = curr_min_y

        new_max_y = GuiUtility.parse_float(self.ui.lineEdit_maxY)
        if new_max_y is None:
            new_max_y = curr_max_x

        # Resize
        self.ui.graphicsView_main.setXYLimit(new_min_x, new_max_x, new_min_y, new_max_y)

        return

    def do_select_ipts(self):
        """
        :return:
        """
        # TODO

    def do_set_log_options(self):
        """
        Get the different options for set log
        :return:
        """


    def evt_plot_sample_log(self):
        """
        Plot sample log
        :return:
        """
        log_name = str(self.ui.comboBox_logNames.currentText())
        log_name = log_name.replace(' ', '').split('(')[0]
        self._currentLogIndex = int(self.ui.comboBox_logNames.currentIndex())

        self.plot_sample_log(log_name)

        return

    def get_splitters(self):
        """ Get splitters set up by user.  Called by parent algorithm
        :return:
        """
        return self.ui.tableWidget_segments.get_splitter_list()

    def highlite_picker(self, picker_id, flag, color='red'):
        """
        Highlight (by changing color) of the picker selected
        :param picker_id:
        :return:
        """
        if flag is False:
            if picker_id is None:
                for pid in self._myPickerIDList:
                    self.ui.graphicsView_main.update_indicator(pid, 'black')
            else:
                self.ui.graphicsView_main.update_indicator(picker_id, 'black')
        else:
            print 'Picker list: ', self._myPickerIDList, ' for ', picker_id
            for pid in self._myPickerIDList:
                if pid == picker_id:
                    self.ui.graphicsView_main.update_indicator(pid, color)
                else:
                    self.ui.graphicsView_main.update_indicator(pid, 'black')
            # END-FOR
        # END-IF-ELSE

        return

    def locate_picker(self, x_pos, ratio=0.2):
        """ Locate a picker with the new x
        :param x_pos:
        :param ratio:
        :return: 2-tuple (Boolean, Object)
        """
        # Check
        if len(self._myPickerIDList) == 0:
            return False, 'No picker to select!'

        assert isinstance(ratio, float)
        assert (ratio > 0.01) and (ratio <= 0.5)

        print '[DB-DEV] Indicators: ', self._myPickerIDList

        x_lim = self.ui.graphicsView_main.getXLimit()

        # Get the vector of x positions of indicator and
        vec_pos = [x_lim[0]]
        for ind_id in self._myPickerIDList:
            picker_x, picker_y = self.ui.graphicsView_main.get_indicator_position(ind_id)
            vec_pos.append(picker_x)
            print '[DB-DEV] ID ', ind_id, ' at ', picker_x, picker_y
        # END-FOR
        vec_pos.append(x_lim[1])
        print '[DB-DEV] Positions: ', vec_pos
        sorted_vec_pos = sorted(vec_pos)

        # Search
        post_index = numpy.searchsorted(sorted_vec_pos, x_pos)
        if post_index == 0:
            return False, 'Position %f is out of canvas left boundary %f. It is weird!' % (x_pos, vec_pos[0])
        elif post_index >= len(vec_pos):
            return False, 'Position %f is out of canvas right boundary %f. It is weird!' % (x_pos, vec_pos[-1])

        pre_index = post_index - 1
        dx = sorted_vec_pos[post_index] - sorted_vec_pos[pre_index]
        return_index = -1
        if sorted_vec_pos[pre_index] <= x_pos <= sorted_vec_pos[pre_index] + dx * ratio:
            return_index = pre_index
        elif sorted_vec_pos[post_index] - dx * ratio <= x_pos <= sorted_vec_pos[post_index]:
            return_index = post_index
        if return_index >= 0:
            nearest_picker_x = sorted_vec_pos[return_index]
            raw_index = vec_pos.index(nearest_picker_x)
        else:
            raw_index = return_index

        # correct for index=0 is boundary
        raw_index -= 1

        return raw_index

    def menu_select_nearest_picker(self):
        """ Select nearest picker
        :return:
        """
        print '[DB] Select picker near %f ....' % self._currMousePosX
        # Get all the pickers' position
        picker_pos_list = self.ui.tableWidget_segments.get_start_times()

        # Find the nearest picker
        picker_pos_list.append(self._currMousePosX)
        picker_pos_list.sort()
        index = picker_pos_list.index(self._currMousePosX)

        prev_index = index - 1
        next_index = index + 1

        select_picker_pos = picker_pos_list[prev_index]

        if next_index < len(picker_pos_list) and \
            abs(picker_pos_list[next_index] - self._currMousePosX) < \
                        abs(picker_pos_list[prev_index] - self._currMousePosX):
            select_picker_pos = picker_pos_list[next_index]
        print 'Selected picker is at %.5f' % select_picker_pos

        # Add the information to graphics
        self._currentPickerID = self.ui.graphicsView_main.get_indicator_key(select_picker_pos, None)
        self._myPickerMode = IN_PICKER_MOVING

        return

    def menu_quit_picker_selection(self):
        """ Quit picker-selecion mode
        :return:
        """
        print 'Cancel picker selection'
        self._myPickerMode = OUT_PICKER

        return

    def on_mouse_press_event(self, event):
        """ If in the picking up mode, as mouse's left button is pressed down,
        the indicator/picker
        is in the moving mode

        event.button has 3 values:
         1: left
         2: middle
         3: right
        """
        # Get event data
        x = event.xdata
        y = event.ydata
        button = event.button
        print "[DB] Button %d is (pressed) down at (%s, %s)." % (button, str(x), str(y))

        # Select situation
        if x is None or y is None:
            # mouse is out of canvas, return
            return

        if button == 1:
            # left button
            if self._myPickerMode == IN_PICKER:
                # allowed status to in picker-moving status
                self._myPickerMode = IN_PICKER_MOVING

        return

    def on_mouse_release_event(self, event):
        """ If the left button is released and prevoiusly in IN_PICKER_MOVING mode,
        then the mode is over
        """
        button = event.button

        self._currMousePosX = event.xdata
        self._currMousePosY = event.ydata

        if button == 1:
            if self._myPickerMode == IN_PICKER_MOVING:
                self._myPickerMode = IN_PICKER

        elif button == 3:
            if self._myPickerMode == IN_PICKER_SELECTION:
                # Pop-out menu
                self.ui.menu = QtGui.QMenu(self)

                action1 = QtGui.QAction('Select', self)
                action1.triggered.connect(self.menu_select_nearest_picker)
                self.ui.menu.addAction(action1)

                action2 = QtGui.QAction('Cancel', self)
                action2.triggered.connect(self.menu_quit_picker_selection)
                self.ui.menu.addAction(action2)

                # add other required actions
                self.ui.menu.popup(QtGui.QCursor.pos())

        return

    def on_mouse_motion(self, event):
        """ Event handling in case mouse is moving
        """
        new_x = event.xdata
        new_y = event.ydata

        # Outside of canvas, no response
        if new_x is None or new_y is None:
            return

        # Calculate the relative displacement
        dx = new_x - self._currMousePosX
        dy = new_y - self._currMousePosY

        x_min, x_max = self.ui.graphicsView_main.getXLimit()
        mouse_resolution_x = (x_max - x_min) * 0.001
        y_min, y_max = self.ui.graphicsView_main.getYLimit()
        mouse_resolution_y = (y_max - y_min) * 0.001

        if self._myPickerMode == IN_PICKER_MOVING:
            # Respond to motion of mouse and move the indicator
            if abs(dx) > mouse_resolution_x or abs(dy) > mouse_resolution_y:
                # it is considered that the mouse is moved
                self._currMousePosX = new_x
                self._currMousePosY = new_y
                # self.ui.graphicsView_main.move_indicator(self._currentPickerID, dx, dy)

                self.ui.graphicsView_main.set_indicator_position(self._currentPickerID, new_x, new_y)

                print '[DB]', 'New X = ', new_x
            # END-IF(dx, dy)

        elif self._myPickerMode == IN_PICKER_SELECTION:
            # Highlight (change color) a picker and set the picker/indicator in active mode
            if abs(dx) > mouse_resolution_x:
                # Consider the picker by time only
                picker_list_index = self.locate_picker(x_pos=new_x, ratio=0.2)
                if picker_list_index == -2:
                    print 'Middle of nowhere'
                elif picker_list_index == -1:
                    print 'Left boundary'
                elif picker_list_index == len(self._myPickerIDList):
                    print 'Right boundary'
                else:
                    print 'Pick indicator %d of %d' % (picker_list_index, len(self._myPickerIDList))
                self.highlite_picker(picker_id=None, flag=False)
                if 0 <= picker_list_index < len(self._myPickerIDList):
                    picker_id = self._myPickerIDList[picker_list_index]
                    self.highlite_picker(picker_id, True)
            # END-IF

        # END-IF (PickerMode)

        return

    def set_run(self, run_number):
        """
        Set run
        :return:
        """
        run_number = int(run_number)
        self.ui.lineEdit_runNumber.setText('%d' % run_number)

        return

    def setup(self):
        """ Set up from parent main window
        :return:
        """
        ipts_run_dict = self._myParent.get_ipts_runs()

        # Set to tree
        for ipts in ipts_run_dict.keys():
            run_list = ipts_run_dict[ipts]
            self.ui.treeView_iptsRun.add_ipts_runs(ipts, run_list)

        return

    def plot_sample_log(self, sample_log_name):
        """

        :param sample_log_name:
        :return:
        """
        vec_x, vec_y = self._myParent.get_sample_log_value(sample_log_name, relative=True)

        self.ui.graphicsView_main.clear_all_lines()
        self.ui.graphicsView_main.add_plot_1d(vec_x, vec_y, label=sample_log_name)

        return


def testmain(argv):
    """ Main method for testing purpose
    """
    parent = None

    app = QtGui.QApplication(argv)

    # my plot window app
    myapp = WindowLogPicker(parent)
    myapp.show()

    exit_code=app.exec_()
    sys.exit(exit_code)

    return

if __name__ == "__main__":
    testmain(sys.argv)
