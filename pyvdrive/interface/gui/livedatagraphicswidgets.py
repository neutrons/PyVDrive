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
        self._currMainLineKey = None  # use label_y as key
        self._currRightLineKey = None  # use label_y as key

        self._mainLineIndex = None
        self._rightLineIndex = None

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
            if y_label == self._currMainLineKey:
                update = True
            elif self._mainLineIndex is not None:
                # remove current plot
                self.remove_line(0, 0, self._mainLineIndex)
        else:
            if y_label == self._currRightLineKey:
                update = True
            elif self._rightLineIndex is not None:
                # remove current plot
                self.remove_line(0, 0, self._rightLineIndex)

        # set default color
        if color is None:
            color = 'blue'

        # plot (new or update)
        if update:
            if is_main:
                line_key = self._mainLineIndex
            else:
                line_key = self._rightLineIndex
            self.update_line(row_index=0, col_index=0, ikey=line_key, vec_x=time_vec, vec_y=value_vec, is_main=is_main)

        else:
            line_key = self.add_plot(time_vec, value_vec, is_right=not is_main,
                                     y_label=y_label, label=line_label,
                                     line_style=line_style, marker=marker,
                                     color=color)

            # update information
            if is_main:
                self._currMainLineKey = y_label
                self._mainLineIndex = line_key
            else:
                self._currRightLineKey = y_label
                self._rightLineIndex = line_key
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
            self._currMainLineKey = None
            self._mainLineIndex = None

        if include_right:
            if (0, 0) in self.canvas().axes_right:
                # it does exist
                self._currRightLineKey = None
                self._rightLineIndex = None
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
