# Zoo of graphics view widgets for "Live Data"
import numpy

from mplgraphicsview import MplGraphicsView
from mplgraphicsview1d import MplGraphicsView1D
from mplgraphicsview2d import MplGraphicsView2D


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
            line_key = self.add_plot(time_vec, vec_y, is_right=not is_main,
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

            print '[DB...BAT] Multi-Plot  Y-label vs Line-label: {0} vs {1}.  Time 0 = {2}.  Side = {3}. ' \
                  'Y-range: {4}, {5}' \
                  ''.format(y_label, label_line, time_vec[0], is_main, numpy.min(vec_y), numpy.max(vec_y))
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
            self.update_line(row_index=0, col_index=0, ikey=line_key, vec_x=time_vec, vec_y=value_vec, is_main=is_main)

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

        print '[DB...BAT] Y-label vs Line-label: {0} vs {1}.  Time 0 = {2}.  Side = {3}' \
              ''.format(y_label, line_label, time_vec[0], is_main)

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

    def plot_contour(self, data_set_dict):
        """ Plot 2D data as a contour plot
        :param data_set_dict: dictionary such that
        :return:
        """
        # Check inputs
        assert isinstance(data_set_dict, dict), 'Input data must be in a dictionary but not a {0}' \
                                                ''.format(type(data_set_dict))

        # construct
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

            # vector Y: each row will have the value of a pattern
            matrix_y[matrix_index:] = data_set_dict[index][1]  #
            matrix_index += 1
        # END-FOR

        # clear canvas and add contour plot
        self.clear_canvas()
        self.canvas().add_contour_plot(vec_x, vec_y, matrix_y)

        return


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

        self._minX = None
        self._maxX = None

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

    def plot_previous_run(self, vec_x, vec_y, line_color, line_label, unit):
        """

        :return:
        """
        # TODO/ISSUE/NOW - Use update instead of delete and move

        # delete previous one (if they are different)
        if self._previousRunID is not None:
            self.remove_line(self._previousRunID)
            self._previousRunKey = None

        # update
        self._previousRunID = self.add_plot_1d(vec_x, vec_y, color=line_color,
                                               label=line_label, x_label=unit)

        # set Y label
        max_y = max(vec_y) * 1.05
        self.setXYLimit(ymin=0, ymax=max_y)

        return

    def plot_current_plot(self, vec_x, vec_y, line_color, line_label, unit):
        """
        update/plot current accumulated
        :return:
        """
        # TODO/ISSUE/NOW - Use update instead of delete and move

        # remove existing line
        if self._currentRunID is not None:
            self.remove_line(self._currentRunID)

        # plot
        self._currentRunID = self.add_plot_1d(vec_x, vec_y, color=line_color,
                                              label=line_label, x_label=unit)

        if self._previousRunID is None:
            max_y = max(vec_y) * 1.05
            self.setXYLimit(ymin=0, ymax=max_y)

        return

    def rescale_y_axis(self, x_min=None, x_max=None):
        """
        rescale Y axis range automatically and considering showing range of X-axis too!
        :return:
        """
        if x_min is None:
            if self._minX is None:
                raise RuntimeError('Rescale Y Axis requires x-min shall be given!')
            else:
                x_min = self._minX

        if x_max is None:
            if self._maxX is None:
                raise RuntimeError('Rescale Y axis requires x-max shall be given!')
            else:
                x_max = self._maxX

        # retrieve vec X and vec Y from plot and find min and max on subset of Y
        y_min = None
        y_max = None
        for line_id in [self._currentRunID, self._previousRunID]:
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
