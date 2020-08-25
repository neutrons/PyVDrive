# Zoo of graphics view widgets for "Live Data"
import numpy

from pyvdrive.interface.gui.mplgraphicsview import MplGraphicsView
from pyvdrive.interface.gui.mplgraphicsview1d import MplGraphicsView1D
from pyvdrive.interface.gui.mplgraphicsview2d import MplGraphicsView2D
from pyvdrive.core import datatypeutility


class GeneralPurpose1DView(MplGraphicsView1D):
    """
    1D canvas for general-purpose
    """
    def __init__(self, parent):
        """
        initialization
        :param parent:
        """
        # initialization
        super(GeneralPurpose1DView, self).__init__(parent, 1, 1)

        # register for the class variables
        # for sample logs
        self._currMainAxisName = None  # use label_y as key
        self._currRightAxisName = None  # use label_y as key

        self._mainAxisLogLineKey = None
        self._rightAxisLogLineKey = None

        # peak parameters
        self._mainAxisPeakParamLineKey = {1: None, 2: None, 3: None}
        self._rightAxisPeakParamLineKey = {1: None, 2: None, 3: None}

        # color
        self._peakParamColor = {1: 'red', 2: 'green', 3: 'black'}

        return

    def clear_axis(self, is_main):
        """
        blabla
        :param is_main:
        :return:
        """
        # check whether need to remove previous plot
        if is_main:
            if self._mainAxisLogLineKey is not None:
                # log
                self.remove_line(0, 0, self._mainAxisLogLineKey)
                self._mainAxisLogLineKey = None
            else:
                # peak parameters
                for bank_id in self._mainAxisPeakParamLineKey.keys():
                    if self._mainAxisPeakParamLineKey[bank_id] is not None:
                        self.remove_line(0, 0, self._mainAxisPeakParamLineKey[bank_id])
                        self._mainAxisPeakParamLineKey[bank_id] = None

        else:
            if self._rightAxisLogLineKey is not None:
                # log
                self.remove_line(0, 0, self._rightAxisLogLineKey)
                self._rightAxisLogLineKey = None
            else:
                # peak parameters
                for bank_id in self._rightAxisPeakParamLineKey.keys():
                    if self._rightAxisPeakParamLineKey[bank_id] is not None:
                        self.remove_line(0, 0, self._rightAxisPeakParamLineKey[bank_id])
                        self._rightAxisPeakParamLineKey[bank_id] = None
        # END-IF-ELSE

        return

    def is_same(self, is_main, plot_param_name):
        """

        :param is_main:
        :param plot_param_name:
        :return:
        """
        # check ...
        # TODO ASAP
        # blabla
        if is_main:
            return plot_param_name == self._currMainAxisName

        return plot_param_name == self._currRightAxisName

    def plot_peak_parameters(self, vec_time, peak_value_bank_dict, param_name, is_main):
        """
        blabla
        :param vec_time:
        :param peak_value_bank_dict:
        :param param_name:
        :param is_main:
        :return:
        """
        # check ... blabla TODO/ASAP check
        # ... ...

        # marker
        if param_name.lower().count('intensity'):
            marker = 'D'
            line_style = ':'
        else:
            marker = '*'
            line_style = '--'

        # check whether need to remove previous plot
        if is_main and self._mainAxisLogLineKey is not None:
            self.remove_line(0, 0, self._mainAxisLogLineKey)
            self._mainAxisLogLineKey = None
        elif is_main is False and self._rightAxisLogLineKey is not None:
            self.remove_line(0, 0, self._rightAxisLogLineKey)
            self._rightAxisLogLineKey = None

        # get banks
        bank_id_list = sorted(peak_value_bank_dict.keys())

        for bank_id in bank_id_list:
            y_label = '{0} Bank {1}'.format(param_name, bank_id)

            # update or new line
            if is_main:
                line_key = self._mainAxisPeakParamLineKey[bank_id]
            else:
                line_key = self._rightAxisPeakParamLineKey[bank_id]
            if line_key is None:
                update = False
            else:
                update = True

            if update:
                self.update_line(0, 0, ikey=line_key, is_main=is_main,
                                 vec_x=vec_time, vec_y=peak_value_bank_dict[bank_id],
                                 line_style=line_style, line_color=self._peakParamColor[bank_id],
                                 marker=marker, marker_color=self._peakParamColor[bank_id])

            else:
                line_key = self.add_plot(vec_time, peak_value_bank_dict[bank_id],
                                         is_right=not is_main,
                                         y_label=y_label, label=y_label,
                                         line_style=line_style, marker=marker,
                                         color=self._peakParamColor[bank_id])
                if is_main:
                    self._mainAxisPeakParamLineKey[bank_id] = line_key
                else:
                    self._rightAxisPeakParamLineKey[bank_id] = line_key
            # END-IF
        # END-FOR

        return

    def plot_multi_data_set(self, vec_x_list, vec_y_list, y_label, plot_setup_list, is_main):
        """
        plot multiple data set on one axis
        :param vec_x_list:
        :param vec_y_list:
        :param y_label:
        :param plot_setup_list:
        :param is_main:
        :return:
        """
        # it shall be straightforward to remove the lines
        # FIXME - this is a brute force solution!  Need to be more smart for efficiency
        if is_main:
            include_main = True
            include_right = False
        else:
            include_main = False
            include_right = True

        self.remove_all_plots(include_main=include_main, include_right=include_right)

        num_plots = len(vec_x_list)
        min_y = max_y = None

        # plot individual
        axis_color = None
        last_time = None
        for i_plot in range(num_plots):
            time_vec = vec_x_list[i_plot]
            vec_y = vec_y_list[i_plot]
            label_line, color, marker, line_style = plot_setup_list[i_plot]

            # do some statistic
            if min_y is None or min_y > numpy.min(vec_y):
                min_y = numpy.min(vec_y)
            if max_y is None or max_y < numpy.max(vec_y):
                max_y = numpy.max(vec_y)
            # END-IF

            # plot
            self.add_plot(time_vec, vec_y, is_right=not is_main,
                          y_label=y_label, label=label_line,
                          line_style=line_style, marker=marker,
                          color=color)
            axis_color = color
            last_time = time_vec[-1]

            # update information
            # FIXME - how to REMEMBER! line_key
            # if is_main:
            #     self._currMainLineKey = y_label
            #     self._mainLineIndex = line_key
            # else:
            #     self._currRightLineKey = y_label
            #     self._rightLineIndex = line_key
            # # END-IF

            print('[DB...BAT] Multi-Plot  Y-label vs Line-label: {0} vs {1}.  Time 0 = {2}.  Side = {3}.'
                  'Y-range: {4}, {5}'
                  ''.format(y_label, label_line, time_vec[0], is_main, numpy.min(vec_y), numpy.max(vec_y)))
        # END-FOR

        # set the Y-axis color
        self.set_axis_color(row_index=0, col_index=0, is_main=is_main, color=axis_color)

        # set the X-axis range
        self.canvas().set_x_limits(row_index=0, col_index=0, xmin=-1, xmax=last_time+6, is_main=True,
                                   is_right=True, apply_change=True)
        # scale Y
        y_range = max_y - min_y
        if y_range < 1.E-5:
            y_range = abs(min_y)
        self.canvas().set_y_limits(row_index=0, col_index=0, is_main=is_main, ymin=min_y - 0.02 * y_range,
                                   ymax=max_y + 0.02 * y_range, apply_change=True)

        # set legend
        self.canvas()._setup_legend(0, 0, location='"upper left"', is_main=is_main)

        return

    def plot_sample_log(self, time_vec, value_vec, is_main, x_label, y_label, line_label,
                        line_style, marker, color):
        """ Requirements
        1. compare with currently plotted sample to determine whether it is to remove current plot and plot a new
           line or update current line
        2. determine color style and etc.

        plot sample log or other X-Y data
        :param time_vec:
        :param value_vec:
        :param is_main:
        :param x_label:
        :param y_label:
        :param line_label:
        :param line_style:
        :param marker:
        :param color:
        :return:
        """
        # determine whether it is to update the current
        update = False

        if is_main:
            if y_label == self._currMainAxisName:
                update = True
            elif self._mainAxisLogLineKey is not None:
                # remove current plot
                self.remove_line(0, 0, self._mainAxisLogLineKey)
        else:
            if y_label == self._currRightAxisName:
                update = True
            elif self._rightAxisLogLineKey is not None:
                # remove current plot
                self.remove_line(0, 0, self._rightAxisLogLineKey)

        # set default color
        if color is None:
            color = 'blue'

        # plot (new or update)
        if update:
            if is_main:
                line_key = self._mainAxisLogLineKey
            else:
                line_key = self._rightAxisLogLineKey
            try:
                self.update_line(row_index=0, col_index=0, ikey=line_key, vec_x=time_vec, vec_y=value_vec,
                                 is_main=is_main)
            except ValueError as val_err:
                print('Failed to update {0} with time {1} and value {2} due to {3}.'
                      ''.format(y_label, time_vec, value_vec, val_err))
                raise val_err

        else:
            line_key = self.add_plot(time_vec, value_vec, is_right=not is_main,
                                     y_label=y_label, label=line_label,
                                     line_style=line_style, marker=marker,
                                     color=color)

            # update information
            if is_main:
                self._currMainAxisName = y_label
                self._mainAxisLogLineKey = line_key
            else:
                self._currRightAxisName = y_label
                self._rightAxisLogLineKey = line_key
        # END-IF

        # set the Y-axis color
        self.set_axis_color(row_index=0, col_index=0, is_main=is_main, color=color)

        # set the X-axis range
        last_time = time_vec[-1]
        self.canvas().set_x_limits(row_index=0, col_index=0, xmin=-1, xmax=last_time+6, is_main=True,
                                   is_right=True, apply_change=True)
        # scale Y
        min_y = numpy.min(value_vec)
        max_y = numpy.max(value_vec)
        y_range = max_y - min_y
        if y_range < 1.E-5:
            y_range = abs(min_y)
        self.canvas().set_y_limits(row_index=0, col_index=0, is_main=is_main, ymin=min_y - 0.02 * y_range,
                                   ymax=max_y + 0.02 * y_range, apply_change=True)

        print('[DB...BAT] Y-label vs Line-label: {0} vs {1}.  Time 0 = {2}.  Side = {3}'
              ''.format(y_label, line_label, time_vec[0], is_main))

        # set legend
        self.canvas()._setup_legend(0, 0, location='"lower left"', is_main=is_main)

        return

    def remove_all_plots(self, include_main=True, include_right=True):
        """
        remove all the plots on the line
        :param include_main:
        :param include_right:
        :return:
        """
        # reset the records
        if include_main:
            self._currMainAxisName = None
            self._mainAxisLogLineKey = None

        if include_right:
            if (0, 0) in self.canvas().axes_right:
                # it does exist
                self._currRightAxisName = None
                self._rightAxisLogLineKey = None
            else:
                # it is not initialized yet
                include_right = False

        # clear the line
        self.clear_all_lines(row_number=0, col_number=0, include_main=include_main, include_right=include_right)

        return


class Live2DView(MplGraphicsView2D):
    """
    canvas for visualization of multiple reduced data in 2D
    """
    def __init__(self, parent):
        """
        initialization on 2D view
        :param parent:
        """
        super(Live2DView, self).__init__(parent)

        return

    # TEST - 20180730
    def evt_toolbar_home(self):
        """
        @return:
        """
        super(Live2DView, self).evt_toolbar_home()

        # zoom the image back???

        return

    def plot_contour(self, data_set_dict):
        """ Plot 2D data as a contour plot
        :param data_set_dict: dictionary such that
        :return:
        """
        # Check inputs
        # Check inputs
        datatypeutility.check_dict('Input data set', data_set_dict)

        # TEST/TODO - Find out the status in real time test
        print('[DB...FIND] About to plot contour... Is Zoom From Home = {}, Home XY Limit = {}, '
              'Current X limit = {}'.format(self._isZoomedFromHome, self._homeXYLimit,
                                            self._zoomInXRange))

        # record current setup
        if self.has_image_on_canvas():
            print('[DB...BAT] Do I have Image? {}'.format(self.has_image_on_canvas()))
            self._zoomInXRange = self.canvas.getXLimit()

        # construct the vectors for 2D contour plot
        x_list = sorted(data_set_dict.keys())
        vec_x = data_set_dict[x_list[0]][0]
        vec_y = numpy.array(x_list)
        size_x = len(vec_x)

        # create matrix on mesh
        grid_shape = len(vec_y), len(vec_x)
        matrix_y = numpy.ndarray(grid_shape, dtype='float')
        matrix_index = 0
        for index in vec_y:
            # vector X
            vec_x_i = data_set_dict[index][0]
            if len(vec_x_i) != size_x:
                raise RuntimeError('Unable to form a contour plot because {0}-th vector has a different size {1} '
                                   'than first size {2}'.format(index, len(vec_x_i), size_x))
            # END-IF
            # vector Y: each row will have the value of a pattern

            matrix_y[matrix_index] = data_set_dict[index][1]
            matrix_index += 1

        # END-FOR

        # plot
        self.canvas.add_contour_plot(vec_x, vec_y, matrix_y)

        if self._zoomInXRange is None:
            # no zoom in: set to user defined
            x_min = 0.3
            x_max = 3.0
        else:
            # zoom is pressed down and already zoomed
            x_min = self._zoomInXRange[0]
            x_max = self._zoomInXRange[1]
        self.setXYLimit(xmin=x_min, xmax=x_max)

        # update flag
        self._hasImage = True

        return
# END-DEF-CLASS ()


class SingleBankView(MplGraphicsView):
    """
    extended for visualizing single bank data in Live data view
    """
    def __init__(self, parent):
        """

        :param parent:
        """
        super(SingleBankView, self).__init__(parent)

        # holder of ID
        self._currentRunID = None
        self._currentRunKey = None  # can use workspace name

        self._previousRunID = None
        self._previousRunKey = None  # can use workspace name

        # original X range
        self._dataXMin = None
        self._dataXMax = None

        # region of interest
        self._roiMin = None
        self._roiMax = None

        return

    def delete_previous_run(self):
        """

        :return:
        """
        # remove/delete line
        if self._previousRunID is not None:
            self.remove_line(self._previousRunID)

        # reset
        self._previousRunID = None
        self._previousRunKey = None

        return

    def get_data(self, x_min, x_max, is_currents=True):
        """

        :param x_min:
        :param x_max:
        :return:
        """
        if is_currents:
            result = self.canvas().get_data(self._currentRunID)
        else:
            result = self.canvas().get_data(self._previousRunID)

        # get vector X and vector Y
        vec_x, vec_y = result
        assert len(vec_x) == len(vec_y), 'Vector X and Y\'s sizes shall be same.'

        i_min = numpy.searchsorted(vec_x, x_min, side='left', sorter=None)
        i_max = numpy.searchsorted(vec_x, x_max, side='left', sorter=None)

        return vec_x[i_min:i_max], vec_y[i_min:i_max]

    def plot_previous_run(self, vec_x, vec_y, line_color, line_label):
        """
        Plot previous run
        :param vec_x:
        :param vec_y:
        :param line_color:
        :param line_label:
        :return:
        """
        # delete previous one (if they are different)
        if self._previousRunID is None:
            # add a new plot
            self._previousRunID = self.add_plot_1d(vec_x, vec_y, color=line_color,
                                                   label=line_label)
        else:
            # update the previous plot
            self.updateLine(ikey=self._previousRunID, vecx=vec_x, vecy=vec_y, label=line_label)
        # END-IF-ELSE

        return

    def plot_current_plot(self, vec_x, vec_y, line_color, line_label, unit, auto_scale_y):
        """ update/plot current one that is being accumulated
        :param vec_x:
        :param vec_y:
        :param line_color:
        :param line_label:
        :param unit:
        :param auto_scale_y:
        :return:
        """
        # reset X
        self._dataXMin = vec_x[0]
        self._dataXMax = vec_x[-1]

        if self._currentRunID is None:
            # new line
            self._currentRunID = self.add_plot_1d(vec_x, vec_y, color=line_color,
                                                  label=line_label, x_label=unit)
        else:
            # update line
            self.canvas().updateLine(ikey=self._currentRunID, vecx=vec_x, vecy=vec_y,
                                     linecolor=line_color, label=line_label)
            if unit is not None:
                self.canvas().set_xy_label(side='x', text=unit)

        # END-IF-ELSE

        # scale Y
        if auto_scale_y:
            self.rescale_y_axis(x_min=None, x_max=None)

        return

    def rescale_y_axis(self, x_min=None, x_max=None):
        """
        rescale Y axis range automatically and considering showing range of X-axis too!
        :return:
        """
        if x_min is None:
            if self._roiMin is not None:
                x_min = self._roiMin
            elif self._dataXMin is not None:
                x_min = self._dataXMin
            else:
                raise RuntimeError('Rescale Y Axis requires x-min shall be given!')
        # END-IF

        if x_max is None:
            if self._roiMax is not None:
                x_max = self._roiMax
            elif self._dataXMax is not None:
                x_max = self._dataXMax
            else:
                raise RuntimeError('Rescale Y axis requires x-max shall be given!')

        # retrieve vec X and vec Y from plot and find min and max on subset of Y
        # check line ID
        if self._currentRunID is None:
            raise RuntimeError('It is not possible to have current run ID as None.')
        else:
            line_id_list = [self._currentRunID]
        if self._previousRunID is not None:
            line_id_list.append(self._previousRunID)

        y_min = None
        y_max = None
        for line_id in line_id_list:
            # get data
            vec_x, vec_y = self.canvas().get_data(line_id)
            # search indexes
            i_min, i_max = numpy.searchsorted(vec_x, [x_min, x_max])
            # find Y range
            y_min_i = numpy.min(vec_y[i_min:i_max])
            y_max_i = numpy.max(vec_y[i_min:i_max])
            # compare
            if y_min is None or y_min_i < y_min:
                y_min = y_min_i
            if y_max is None or y_max_i > y_max:
                y_max = y_max_i
        # END-FOR

        # set Y limit
        y_range = y_max - y_min
        upper_y = y_max + 0.05 * y_range
        lower_y = 0   # intensity cannot be zero but shall always from zero
        self.setXYLimit(ymin=lower_y, ymax=upper_y)

        return

    def reset_roi(self):
        """
        reset region of interest to range of data.  And apply to figure
        :return:
        """
        self._roiMin = None
        self._roiMax = None

        self.setXYLimit(xmin=self._dataXMin, xmax=self._dataXMax)

        return

    def set_roi(self, x_min, x_max):
        """
        set ROI and apply to the figure
        :param x_min:
        :param x_max:
        :return:
        """
        # X-MIN
        if x_min is not None:
            # set region of interest if x_min is specified
            self._roiMin = x_min
        else:
            # use the previously defined region of interest's x_min.
            # or None if never been defined
            x_min = self._roiMin

        # X-Max
        if x_max is not None:
            # set region of interest if x_min is specified
            self._roiMax = x_max
        else:
            # use the previously defined region of interest's x_min.
            # or None if never been defined
            x_max = self._roiMax

        self.setXYLimit(xmin=x_min, xmax=x_max)

        return
