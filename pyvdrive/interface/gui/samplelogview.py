import numpy as np
import bisect
try:
    import qtconsole.inprocess
    from PyQt5 import QtCore
    from PyQt5.QtWidgets import QMenu, QAction
    from PyQt5.QtGui import QCursor
except ImportError:
    from PyQt4 import QtCore
    from PyQt4.QtGui import QMenu, QAction, QCursor
import mplgraphicsview
from pyvdrive.lib import datatypeutility
from pyvdrive.lib import vdrivehelper

COLOR_LIST = ['red', 'green', 'black', 'cyan', 'magenta', 'yellow']


class LogGraphicsView(mplgraphicsview.MplGraphicsView):
    """
    Class ... extends ...
    for specific needs of the graphics view for interactive plotting of sample log,

    Note:
    1. each chopper-slicer picker is a vertical indicator
       (ideally as a picker is moving, a 2-way indicator can be shown on the canvas
    """
    # define signals
    mySlicerUpdatedSignal = QtCore.pyqtSignal(list)  # signal as the slicers updated

    def __init__(self, parent):
        """
        Purpose
        :return:
        """
        # Base class constructor
        mplgraphicsview.MplGraphicsView.__init__(self, parent)

        # parent window (logical parent)
        self._myParent = None

        # GUI property
        self.menu = None

        # collection of indicator IDs that are on canvas
        self._currentLogPickerList = list()   # list of indicator IDs.
        self._pickerRangeDict = dict()  # dictionary for picker range. key: position, value: indicator IDs

        # resolution to find
        self._resolutionRatio = 0.001  # resolution to check mouse position
        self._pickerRangeRatio = 0.01  # picker range = (X_max - X_min) * ratio
        self._pickerRange = None  # picker range
        self._currXLimit = (0., 1.)  # 2-tuple as left X limit and right X limit

        # manual slicer picker mode
        self._inManualPickingMode = False
        # mouse mode
        self._mouseLeftButtonHold = False

        # current plot IDs
        self._currPlotID = None
        self._currentSelectedPicker = None
        self._currMousePosX = None
        self._currMousePosY = None

        # about a selected picker
        self._leftPickerLimit = None
        self._rightPickerLimit = None

        # register dictionaries
        self._sizeRegister = dict()

        # extra title message
        self._titleMessage = ''

        # container for segments plot
        self._splitterSegmentsList = list()

        # define the event handling methods
        self._myCanvas.mpl_connect('button_press_event', self.on_mouse_press_event)
        self._myCanvas.mpl_connect('button_release_event', self.on_mouse_release_event)
        self._myCanvas.mpl_connect('motion_notify_event', self.on_mouse_motion)

        return

    def _calculate_distance_to_nearest_indicator(self, pos_x):
        """
        calculate the distance between given position X to its nearest indicator
        :param pos_x:
        :return: 2-tuple.  nearest distance and indicator ID of the nearest indicator
        """
        def nearest_data(array, x):
            """
            find out the nearest value in a sorted array against given X
            :param array:
            :param x:
            :return: distance and the index of the nearest item in the array
            """
            right_index = bisect.bisect_left(array, x)
            left_index = right_index - 1

            if left_index < 0:
                # left to Index=0
                nearest_index = 0
                distance = array[0] - x
            elif right_index == len(array):
                # right to Index=-1
                nearest_index = left_index
                try:
                    distance = x - array[left_index]
                except TypeError as type_err:
                    print '[DB...BAT] x = {0}, array = {1}'.format(x, array)
                    raise type_err
            else:
                dist_left = x - array[left_index]
                dist_right = array[right_index] - x
                if dist_left < dist_right:
                    nearest_index = left_index
                    distance = dist_left
                else:
                    nearest_index = right_index
                    distance = dist_right
            # END-IF-ELSE

            return distance, nearest_index
        # END-DEF

        # return very large number if there is no indicator on canvas
        if len(self._pickerRangeDict) == 0:
            return 1.E22, -1

        # get the indicator positions
        picker_pos_list = self._pickerRangeDict.keys()
        picker_pos_list.sort()

        nearest_picker_distance, nearest_item_index = nearest_data(picker_pos_list, pos_x)
        nearest_picker_position = picker_pos_list[nearest_item_index]
        nearest_picker_id = self._pickerRangeDict[nearest_picker_position]

        return nearest_picker_distance, nearest_picker_id

    def _remove_picker_from_range_dictionary(self, picker_id_to_remove):
        """
        remove an entry in the dictionary by value
        :param picker_id_to_remove:
        :return:
        """
        if False:
            # TODO - TODAY 190 - Remove after testing
            self._pickerRangeDict = {pos_x: picker_id for pos_x, picker_id in
                                     self._pickerRangeDict.items() if picker_id != picker_id_to_remove}
        else:
            for pos_x, picker_id in self._pickerRangeDict.items():
                if picker_id == picker_id_to_remove:
                    del self._pickerRangeDict[pos_x]
        # ...

        return

    def clear_picker(self):
        """
        blabla  will trigger everything including rewrite table!
        :return:
        """
        # remove the picker from the list
        for p_index, picker in enumerate(self._currentLogPickerList):
            # remove from dictionary
            self._remove_picker_from_range_dictionary(picker)
            # remove from canvas
            self.remove_indicator(picker)

        # reset
        self._currentSelectedPicker = None
        self._currentLogPickerList = list()

        # update the new list to parent window
        picker_pos_list = list()
        print ('[DB...BAT] Clear picker: emit signal with empty position list')
        self.mySlicerUpdatedSignal.emit(picker_pos_list)

        return

    def deselect_picker(self):
        """
        de-select the picker by changing its color and reset the flat
        :return:
        """
        assert self._currentSelectedPicker is not None, 'There is no picker that is selected to de-select.'

        self.update_indicator(self._currentSelectedPicker, 'red')
        self._currentSelectedPicker = None

        return

    def get_data_range(self):
        """ Get data range from the 1D plots on canvas
        :return: 4-tuples as min_x, max_x, min_y, max_y
        """
        if len(self._sizeRegister) == 0:
            raise RuntimeError('Unable to get data range as there is no plot on canvas')

        x_min_list = list()
        x_max_list = list()
        y_min_list = list()
        y_max_list = list()

        for value_tuple in self._sizeRegister.values():
            x_min, x_max, y_min, y_max = value_tuple
            x_min_list.append(x_min)
            x_max_list.append(x_max)
            y_min_list.append(y_min)
            y_max_list.append(y_max)
        # END-FOR

        x_min = min(np.array(x_min_list))
        x_max = max(np.array(x_max_list))
        y_min = min(np.array(y_min_list))
        y_max = max(np.array(y_max_list))

        return x_min, x_max, y_min, y_max

    def get_pickers_positions(self):
        """
        get the positions of all pickers on canvas
        :return: a list of floats
        """
        picker_pos_list = self._pickerRangeDict.keys()
        picker_pos_list.sort()

        if True:
            # TODO - TODAY 190 - Remove after testing
            picker_pos_list2 = list()
            for p_id in self._currentLogPickerList:
                pos = self.get_indicator_position(p_id)[0]
                picker_pos_list2.append(pos)
            if set(picker_pos_list) != set(picker_pos_list2):
                raise ArithmeticError('Picker: {} vs {}'.format(picker_pos_list, picker_pos_list2))

        return picker_pos_list

    def menu_add_picker(self):
        """
        add a picker (an indicator) and update the list of pickers' positions to parent
        :return:
        """
        self.add_picker(self._currMousePosX)

        # update to parent window
        # update the new list to parent window
        picker_pos_list = self.get_pickers_positions()
        self.mySlicerUpdatedSignal.emit(picker_pos_list)

        return

    def menu_delete_picker(self):
        """
        delete the selected picker
        :return:
        """
        # check
        if self._currentSelectedPicker is None:
            raise RuntimeError('The prerequisite to delete a picker is to have an already-selected picker.')

        # remove the picker from the list
        p_index = self._currentLogPickerList.index(self._currentSelectedPicker)
        self._currentLogPickerList.pop(p_index)
        # remove from dictionary
        self._remove_picker_from_range_dictionary(self._currentSelectedPicker)
        # remove from canvas
        self.remove_indicator(self._currentSelectedPicker)

        # reset
        self._currentSelectedPicker = None

        # update the new list to parent window
        picker_pos_list = self.get_pickers_positions()
        self.mySlicerUpdatedSignal.emit(picker_pos_list)

        return

    def on_mouse_press_event(self, event):
        """
        determine whether the mode is on
        right button:
            pop out menu if it is relevant
        left button:
            get start to
        :param event:
        :return:
        """
        # only respond when in manual picking mode
        if not self._inManualPickingMode:
            return

        button = event.button
        self._currMousePosX = event.xdata

        if button == 1:
            # left button: if a picker is selected then enter on hold mode
            if self._currentSelectedPicker is not None:
                self._mouseLeftButtonHold = True

        elif button == 3:
            # right button: pop-out menu
            self.menu = QMenu(self)

            if self._currentSelectedPicker is None:
                # no picker is selected
                action1 = QAction('Add Picker', self)
                action1.triggered.connect(self.menu_add_picker)
                self.menu.addAction(action1)

            else:
                # some picker is selected
                action2 = QAction('Delete Picker', self)
                action2.triggered.connect(self.menu_delete_picker)
                self.menu.addAction(action2)

            # add other required actions
            self.menu.popup(QCursor.pos())
        # END-IF-ELSE

        return

    def on_mouse_release_event(self, event):
        """
        left button:
            release the hold-picker mode
        :param event:
        :return:
        """
        # do not respond if it is not in manual picker setup mode
        if not self._inManualPickingMode:
            return

        # determine button and position
        button = event.button

        if button == 1:
            # left button: terminate the state for being on hold
            self._mouseLeftButtonHold = False

        # END-IF

        return

    def on_mouse_motion(self, event):
        """
        If left-button is on hold (and thus a picker is selected, them move the picker)
        otherwise, check whether the cursor is close to any picker enough to select it or far away enough to deselect
                previously selected
        :param event:
        :return:
        """
        # return if not in manual mode
        if not self._inManualPickingMode:
            return

        # return if out of boundary
        if event.xdata is None or event.ydata is None:
            return

        # determine button and position
        # button = event.button
        self._currMousePosX = event.xdata
        self._currMousePosY = event.ydata

        # determine the right position and left position with update of
        if self._currXLimit != self.getXLimit():
            self._currXLimit = self.getXLimit()
            delta_x = self._currXLimit[1] - self._currXLimit[0]
            self._pickerRange = delta_x * self._pickerRangeRatio * 0.5

        # check status
        if self._mouseLeftButtonHold:
            # mouse button is hold with a picker is selected
            # algorithms: if current mouse position is within boundary:
            # 1. update selected indicator (line)'s position AND
            # 2. update the pickerRangeDict
            assert self._currentSelectedPicker is not None, 'In mouse-left-button-hold mode, a picker must be selected.'

            # check whether the selected picker can move
            # print '[DB...BAT] Left limit = ', self._leftPickerLimit, ', Range = ', self._pickerRange
            left_bound = self._leftPickerLimit + self._pickerRange
            right_bound = self._rightPickerLimit - self._pickerRange
            if left_bound < self._currMousePosX < right_bound:
                # free to move
                if False:
                    # TODO - TODAY 190 - Remove after testing
                    self.set_indicator_position(self._currentSelectedPicker, pos_x=self._currMousePosX,
                                                pos_y=self._currMousePosY)
                    # update the position dictionary
                    self._remove_picker_from_range_dictionary(self._currentSelectedPicker)
                    self._pickerRangeDict[self._currMousePosX] = self._currentSelectedPicker
                else:
                    self.update_splitter_picker(self._currentSelectedPicker, self._currMousePosX,
                                                self._currMousePosY)

                # update the pickers' positions with parent window
                updated_picker_positions = self.get_pickers_positions()
                self.mySlicerUpdatedSignal.emit(updated_picker_positions)

            else:
                # unable to move anymore: quit the hold and select to move mode
                self.deselect_picker()
                self._mouseLeftButtonHold = False
            # END-IF-ELSE
        else:
            # mouse button is not hold so need to find out whether the mouse cursor in in a range
            distance, picker_id = self._calculate_distance_to_nearest_indicator(self._currMousePosX)
            # print '[DB...BAT] distance = {0}, Picker ID = {1}, Picker-range = {2}'.format(distance, picker_id,
            #                                                                               self._pickerRange)
            if distance < self._pickerRange:
                # in the range: select picker
                self.select_picker(picker_id)
            elif self._currentSelectedPicker is not None:
                # in the range: deselect picker
                self.deselect_picker()
            # END-IF-ELSE
        # END-IF-ELSE

        return

    def add_picker(self, pos_x):
        """
        add a log picker
        :return:
        """
        # add a picker
        indicator_id = self.add_vertical_indicator(pos_x, color='red', line_width='2')
        # add to dictionary
        self._currentLogPickerList.append(indicator_id)
        # add the picker to the dictionary
        self._pickerRangeDict[pos_x] = indicator_id

        return

    # TODO - TODAY 2019 - In Test
    def update_splitter_picker(self, picker_id, position_x, position_y):
        """
        Update a splitter picker position (existed)
        This operation is not synchronized with its parent' manual splitter setup
        :param picker_id:
        :param position_x:
        :param position_y:
        :return:
        """
        # update the EXISTING indicator position on the figure
        self.set_indicator_position(picker_id, pos_x=position_x, pos_y=position_y)

        # update the position dictionary
        self._remove_picker_from_range_dictionary(picker_id)
        # add back the entry with new position
        self._pickerRangeDict[position_x] = picker_id

        return

    def select_picker(self, picker_id):
        """
        select a slicer picker (indicator) on the canvas
        :param picker_id:
        :return:
        """
        # return if it is the same picker that is already chosen
        if self._currentSelectedPicker == picker_id:
            return

        # previously selected: de-select
        if self._currentSelectedPicker is not None:
            self.deselect_picker()

        # select current on
        self._currentSelectedPicker = picker_id
        self.update_indicator(self._currentSelectedPicker, color='blue')

        # define the pickers to its left and right for boundary
        curr_picker_pos = self.get_indicator_position(picker_id)[0]
        picker_pos_list = sorted(self._pickerRangeDict.keys())
        pos_index = picker_pos_list.index(curr_picker_pos)

        # get the data range for the left most or right most boundary
        x_min, x_max, y_min, y_max = self.get_data_range()

        # determine left boundary
        if pos_index == 0:
            # left most indicator. set the boundary to data's min X
            self._leftPickerLimit = x_min - self._pickerRange
        else:
            self._leftPickerLimit = picker_pos_list[pos_index-1]

        # determine the right boundary
        if pos_index == len(picker_pos_list) - 1:
            # right most indicator. set the boundary to data's max X
            self._rightPickerLimit = x_max + self._pickerRange
        else:
            self._rightPickerLimit = picker_pos_list[pos_index+1]

        return

    def plot_sample_log(self, vec_x, vec_y, sample_log_name, plot_label, sample_log_name_x='Time'):
        """ plot sample log
        :param vec_x:
        :param vec_y:
        :param sample_log_name: on Y-axis
        :param plot_label: label of log to plot
        :param sample_log_name_x: on X-axis
        :return:
        """
        # check
        datatypeutility.check_numpy_arrays('Vector X and Y', [vec_x, vec_y], 1, True)
        datatypeutility.check_string_variable('Sample log name', sample_log_name)
        datatypeutility.check_string_variable('Sample log name (x-axis)', sample_log_name_x)
        datatypeutility.check_string_variable('Plot label', plot_label)

        # set label
        if plot_label == '':
            try:
                plot_label = '%s Y (%f, %f)' % (sample_log_name, min(vec_y), max(vec_y))
            except TypeError as type_err:
                err_msg = 'Unable to generate log with %s and %s: %s' % (
                    str(min(vec_y)), str(max(vec_y)), str(type_err))
                raise TypeError(err_msg)
        # END-IF

        # add plot and register
        self.reset()

        plot_id = self.add_plot_1d(vec_x, vec_y, x_label=sample_log_name_x,
                                   y_label=sample_log_name,
                                   label=plot_label, marker='.', color='blue', show_legend=True)
        self.set_title(title=plot_label)
        self._sizeRegister[plot_id] = (min(vec_x), max(vec_x), min(vec_y), max(vec_y))

        # auto resize
        self.resize_canvas(margin=0.05)
        # re-scale
        # TODO - TONIGHT 3 - FIXME - No self._maxX  self.auto_rescale()
        min_x = vec_x.min()
        max_x = vec_x.max()
        self.setXYLimit(xmin=min_x, xmax=max_x)

        # update
        self._currPlotID = plot_id

        return plot_id

    def plot_chopped_log(self, vec_x, vec_y, sample_log_name_x, sample_log_name_y, plot_label):
        """
        Plot chopped sample log from archive (just points)
        :param vec_x:
        :param vec_y:
        :param sample_log_name_x:
        :param sample_log_name_y:
        :param plot_label:
        :return:
        """
        # check
        datatypeutility.check_numpy_arrays('Vector X and Y', [vec_x, vec_y], 1, True)
        datatypeutility.check_string_variable('Sample log name on Y-axis', sample_log_name_y)
        datatypeutility.check_string_variable('Sample log name on X-axis', sample_log_name_x)
        datatypeutility.check_string_variable('Plot label', plot_label)

        # set label
        if plot_label == '':
            try:
                plot_label = '%s Y (%f, %f)' % (sample_log_name_x, min(vec_y), max(vec_y))
            except TypeError as type_err:
                err_msg = 'Unable to generate log with %s and %s: %s' % (
                    str(min(vec_y)), str(max(vec_y)), str(type_err))
                raise TypeError(err_msg)
        # END-IF

        plot_id = self.add_plot_1d(vec_x, vec_y, x_label=sample_log_name_x,
                                   y_label=sample_log_name_y,
                                   label=plot_label, marker='o', color='red', show_legend=True,
                                   line_style='')
        self._sizeRegister[plot_id] = (min(vec_x), max(vec_x), min(vec_y), max(vec_y))

        # No need to auto resize
        # self.resize_canvas(margin=0.05)
        # re-scale
        if sample_log_name_x.startswith('Time'):
            self.setXYLimit(xmin=0.)
        else:
            min_x = vec_x.min()
            max_x = vec_x.max()
            self.setXYLimit(xmin=min_x, xmax=max_x)

        # # update
        # self._currPlotID = plot_id

        return plot_id

    def remove_slicers(self):
        """
        remove slicers
        :return:
        """
        for slicer_plot_id in self._splitterSegmentsList:
            self.remove_line(slicer_plot_id)

        # clear
        self._splitterSegmentsList = list()

        return

    def reset(self):
        """
        Reset canvas
        :return:
        """
        # dictionary
        self._sizeRegister.clear()

        # clear slicers
        self.remove_slicers()

        # clear all lines
        self.clear_all_lines()
        self._currPlotID = None

        return

    def resize_canvas(self, margin):
        """

        :param margin:
        :return:
        """
        # get min or max
        try:
            x_min, x_max, y_min, y_max = self.get_data_range()
        except RuntimeError:
            # no data left on canvas
            canvas_x_min = 0
            canvas_x_max = 1
            canvas_y_min = 0
            canvas_y_max = 1
        else:
            # get data range
            range_x = x_max - x_min
            canvas_x_min = x_min - 0.05 * range_x
            canvas_x_max = x_max + 0.05 * range_x

            range_y = y_max - y_min
            canvas_y_min = y_min - 0.05 * range_y
            canvas_y_max = y_max + 0.05 * range_y
        # END-IF-ELSE()

        # resize canvas
        self.setXYLimit(xmin=canvas_x_min, xmax=canvas_x_max, ymin=canvas_y_min, ymax=canvas_y_max)

        return

    def set_parent_window(self, parent_window):
        """
        set the parent window (logically parent but not widget in the UI)
        :param parent_window:
        :return:
        """
        self._myParent = parent_window

        # connect signal
        self.mySlicerUpdatedSignal.connect(self._myParent.evt_rewrite_manual_table)

        return

    def set_manual_slicer_setup_mode(self, mode_on):
        """
        set the canvas in the mode to set up slicer manually
        :param mode_on:
        :return:
        """
        assert isinstance(mode_on, bool), 'Mode on/off {0} must be a boolean but not a {1}.' \
                                          ''.format(mode_on, type(mode_on))
        self._inManualPickingMode = mode_on

        # reset all the current-on-select variables
        if mode_on:
            # TODO/ISSUE/33 - Add 2 pickers/indicators at Time[0] and Time[-1] if the table is empty
            pass

            # TODO/ISSUE/33 - Add pickers to if pickers are hidden!
            pass

        else:
            # TODO/ISSUE/33 - Hide all the pickers
            if self._currentSelectedPicker is not None:
                # de-select picker
                self.deselect_pikcer(self._currentSelectedPicker)
                self._currentSelectedPicker = None
            self._currMousePosX = None
            self._currMousePosY = None
            self.clear_picker()

        return

    # TODO - TONIGHT 190 - It is meant to replace show_slicers
    def show_slicers_repetitions(self, vec_slicers_times, vec_target_ws):

        # TODO - FIXME - TODAY 190 - Need a use case for target as REAL string
        vec_target_ws = vec_target_ws.astype('int16')
        unique_target_ws_set = set(vec_target_ws)
        num_segments = len(unique_target_ws_set)
        segment_list = sorted(list(unique_target_ws_set))
        if -1 in segment_list:
            minus_one_index = segment_list.index(-1)
            segment_list.pop(minus_one_index)

        print ('[DB...BAT] Segments: {}'.format(segment_list))

        # construct the data sets for each segments
        seg_dict = dict()
        for seg_id in segment_list:
            seg_dict[seg_id] = None
        # END-FOR

        vec_log_times, vec_log_value = self.canvas().get_data(self._currPlotID)

        print ('[DEBUG...BAT] Log X and Y: size = {}, {}'.format(vec_log_times.shape, vec_log_value.shape))

        for i_target in range(vec_target_ws.shape[0] - 1):
            # ignore the non-interesting section
            if vec_target_ws[i_target] == -1:
                continue
            else:
                target_name_i = vec_target_ws[i_target]

            # from start and stop time to get the index for the current (plotted) log
            t_start = vec_slicers_times[i_target]
            t_stop = vec_slicers_times[i_target + 1]

            # time_index_list = np.searchsorted(vec_log_times, [t_start, t_stop])  # TODO-TEST - replaced!
            time_index_list = vdrivehelper.search_sorted_nearest(vec_log_times, [t_start, t_stop])
            log_time0_index, log_timef_index = time_index_list

            # find the nearest
            if t_start - vec_log_times[log_time0_index-1] < vec_log_times[log_time0_index] - t_start:
                log_time0_index -= 1
            if t_stop - vec_log_times[log_timef_index-1] < vec_log_times[log_timef_index] - t_stop:
                log_timef_index -= 1

            # construct the vector: get the partial for plot
            vec_x_i = vec_log_times[log_time0_index:log_timef_index+1]
            vec_y_i = vec_log_value[log_time0_index:log_timef_index+1]

            print ('[DB...BAT: Locate:  indexes {}:{}'.format(log_time0_index, log_timef_index))

            if seg_dict[target_name_i] is None:
                seg_dict[target_name_i] = vec_x_i, vec_y_i
            else:
                new_vec_x = np.concatenate([seg_dict[target_name_i][0], vec_x_i])
                new_vec_y = np.concatenate([seg_dict[target_name_i][1], vec_y_i])
                seg_dict[target_name_i] = new_vec_x, new_vec_y
        # END-FOR

        # Plot
        num_color = len(COLOR_LIST)  # ['red', 'green', 'black', 'cyan', 'magenta', 'yellow']
        for seg_index, target_index in enumerate(segment_list):
            color_i = COLOR_LIST[seg_index % num_color]
            vec_x_plot, vec_y_plot = seg_dict[seg_index]

            # plot
            seg_plot_index = self.add_plot_1d(vec_x_plot, vec_y_plot, color=color_i,
                                              marker='o', marker_size=3,
                                              line_style='none', line_width=2)
            self._splitterSegmentsList.append(seg_plot_index)
        # END-FOR

        return

    def highlight_slicers(self, vec_times, vec_target_ws, color=None, max_segment_to_show=20):
        """
        show slicers on the canvas by plotting segment of sample logs
        :param vec_times:
        :param vec_target_ws:
        :return:
        """
        print ('[DB...BAT] Vector of times: {}'.format(vec_times))

        # TODO - TONIGHT 190 - Add debugging to this method!
        # check state
        if self._currPlotID is None:
            return True, 'No plot on the screen yet.'

        if len(vec_times) != len(vec_target_ws) + 1:
            raise NotImplementedError('Assumption that input is a histogram! Now vec x size = {},'
                                      'vec y size = {}'.format(vec_times.shape, vec_target_ws.shape))

        # get data from the figure
        # TODO - TODAY 190 - Check whether remove_all_lines() is ever called
        print ('[DB...BAT] Current Plot ID = {}'.format(self._currPlotID))
        vec_x, vec_y = self.canvas().get_data(self._currPlotID)

        print ('[DB...BAT] Sample log vector X range: {}, {}'.format(vec_x[0], vec_x[-1]))
        print ('[DB...BAT] Slicer times range: {}, {}'.format(vec_times[0], vec_times[-1]))

        num_color = len(COLOR_LIST)

        # if there are too many slicing segments, then only shows the first N segments
        if max_segment_to_show is None:
            num_seg_to_show = len(vec_target_ws)
        else:
            datatypeutility.check_int_variable('Maximum segment to show', max_segment_to_show, (1, 100000))
            num_seg_to_show = min(len(vec_target_ws), max_segment_to_show)

        for i_seg in range(num_seg_to_show):
            # get start time and stop time
            # skip the ignored ones
            if vec_target_ws[i_seg] == '-1' or vec_target_ws[i_seg] == -1:
                continue  # skip

            x_start = vec_times[i_seg]
            x_stop = vec_times[i_seg+1]
            print ('[DB...BAT] Segment {}: Time range = {}, {}'.format(i_seg, x_start, x_stop))

            # get start time and stop time's index
            i_start = (np.abs(vec_x - x_start)).argmin()
            i_stop = (np.abs(vec_x - x_stop)).argmin()
            if i_start == i_stop:
                # empty!
                print '[SampleLogView WARNING] splitter start @ {} ({}), stop @ {} ({}). Unable to generate ' \
                      'time segment vector. FYI from index {} to {}: {}' \
                      ''.format(x_start, i_start, x_stop, i_stop, i_start-1, i_stop+1,
                                vec_x[i_start-1:i_stop+2])
                continue
            elif i_start > i_stop:
                raise RuntimeError('It is impossible to have start index {0} > stop index {1}'
                                   ''.format(i_start, i_stop))

            print ('[DB...BAT] Segment {}: Index range = {}, {}'.format(i_seg, i_start, i_stop))

            # get the partial for plot
            vec_x_i = vec_x[i_start:i_stop+1]
            vec_y_i = vec_y[i_start:i_stop+1]

            # plot
            color_index = vec_target_ws[i_seg]
            if color is None:
                if isinstance(color_index, int):
                    color_i = COLOR_LIST[color_index % num_color]
                else:
                    color_i = COLOR_LIST[i_seg % num_color]
            else:
                color_i = color

            seg_plot_index = self.add_plot_1d(vec_x_i, vec_y_i, marker=None, line_style='-', color=color_i,
                                              line_width=2)

            self._splitterSegmentsList.append(seg_plot_index)
        # END-FOR

        status = True
        error_msg = None
        if len(vec_target_ws) > num_seg_to_show:
            status = False
            error_msg = 'There are too many (%d) segments in the slicers.  Only show the first %d.' \
                        '' % (len(vec_target_ws), max_segment_to_show)

        return status, error_msg

    # TODO - TODAY 0 0 0 - Starting from here!  how to highlight/de-highlight slicers!!!
    def remove_slicers_highlights(self, target_name):
        return
