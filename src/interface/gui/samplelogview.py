import GuiUtility as GuiUtility

from PyQt4 import QtGui, QtCore
import mplgraphicsview


class LogGraphicsView(mplgraphicsview.MplGraphicsView):
    """
    Class ... extends ...
    for specific needs of the graphics view for interactive plotting of sample log,
    """
    def __init__(self, parent):
        """
        Purpose
        :return:
        """
        # Base class constructor
        mplgraphicsview.MplGraphicsView.__init__(self, parent)

        return

    def plot_mts_log(self, mts_data_set, log_name):
        """
        Plot MTS log
        :param mts_data_set: a pandas DataFrame
        :param log_name: name of the log to plot
        :return:
        """
        # check inputs
        print '[DB....BAT] plot mts log : input data set is of type %s.' % str(type(mts_data_set))

        assert isinstance(log_name, str), 'Log name %s must be a string but not %s.' \
                                          '' % (str(log_name), str(type(log_name)))

        # parse
        try:
            vec_time = mts_data_set['Time'].values
            vec_log = mts_data_set[log_name].values
        except KeyError as key_err:
            raise RuntimeError('Log name %s does not exist (%s).' % (log_name, str(key_err)))

        # plot
        print '[DB...BAT] Vec X: ', vec_time, type(vec_time)
        print '[DB...BAT] Vec Y: ', vec_log, type(vec_log)
        self.add_plot_1d(vec_x=vec_time, vec_y=vec_log) # , x_label='time (second)', y_label=log_name)

        return

    def plot_sample_log(self, sample_log_name):
        """ Purpose: plot sample log
        Requirement:
        1. sample log name is valid;
        2. resolution is set up (time or maximum number of points)
        Guarantee: canvas is replot
        :param sample_log_name:
        :return:
        """
        # get resolution
        use_time_res = self.ui.radioButton_useTimeResolution.isChecked()
        use_num_res = self.ui.radioButton_useMaxPointResolution.isChecked()
        if use_time_res:
            resolution = GuiUtility.parse_float(self.ui.lineEdit_timeResolution)
        elif use_num_res:
            resolution = GuiUtility.parse_float(self.ui.lineEdit_resolutionMaxPoints)
        else:
            GuiUtility.pop_dialog_error(self, 'Either time or number resolution should be selected.')
            return

        # get the sample log data
        if sample_log_name in self._sampleLogDict[self._currRunNumber]:
            # get sample log value from previous stored
            vec_x, vec_y = self._sampleLogDict[self._currRunNumber][sample_log_name]
        else:
            # get sample log data from driver
            vec_x, vec_y = self._myParent.get_sample_log_value(sample_log_name,
                                                               relative=True)
            self._sampleLogDict[self._currRunNumber][sample_log_name] = vec_x, vec_y

        # get range of the data
        new_min_x = GuiUtility.parse_float(self.ui.lineEdit_minX)
        new_max_x = GuiUtility.parse_float(self.ui.lineEdit_maxX)

        # adjust the resolution
        plot_x, plot_y = process_data(vec_x, vec_y, use_num_res, use_time_res, resolution,
                                      new_min_x, new_max_x)

        # plot
        self.ui.graphicsView_main.clear_all_lines()
        the_label = '%s Y (%f, %f)' % (sample_log_name, min(vec_y), max(vec_y))
        self.ui.graphicsView_main.add_plot_1d(plot_x, plot_y, label=the_label,
                                              marker='.', color='blue')

        # resize canvas
        range_x = plot_x[-1] - plot_x[0]
        new_min_x = (plot_x[0] - range_x * 0.05) if new_min_x is None else new_min_x
        new_max_x = (plot_x[-1] + range_x * 0.05) if new_max_x is None else new_max_x

        range_y = max(plot_y) - min(plot_y)
        new_min_y = GuiUtility.parse_float(self.ui.lineEdit_minY)
        if new_min_y is None:
            new_min_y = min(plot_y) - 0.05 * range_y
        new_max_y = GuiUtility.parse_float(self.ui.lineEdit_maxY)
        if new_max_y is None:
            new_max_y = max(plot_y) + 0.05 * range_y

        self.ui.graphicsView_main.setXYLimit(xmin=new_min_x, xmax=new_max_x,
                                             ymin=new_min_y, ymax=new_max_y)

        return

# END-DEFINITION


def process_data(vec_x, vec_y, use_number_resolution, use_time_resolution, resolution,
                 min_x, max_x):
    """
    re-process the original to plot on canvas smartly
    :param vec_x: vector of time in unit of seconds
    :param vec_y:
    :param use_number_resolution:
    :param use_time_resolution:
    :param resolution: time resolution (per second) or maximum number points allowed on canvas
    :param min_x:
    :param max_x:
    :return:
    """
    # check
    assert isinstance(vec_y, numpy.ndarray) and len(vec_y.shape) == 1
    assert isinstance(vec_x, numpy.ndarray) and len(vec_x.shape) == 1
    assert (use_number_resolution and not use_time_resolution) or (not use_number_resolution and use_time_resolution)

    # range
    if min_x is None:
        min_x = vec_x[0]
    else:
        min_x = max(vec_x[0], min_x)

    if max_x is None:
        max_x = vec_x[-1]
    else:
        max_x = min(vec_x[-1], max_x)

    index_array = numpy.searchsorted(vec_x, [min_x-1.E-20, max_x+1.E-20])
    i_start = index_array[0]
    i_stop = index_array[1]

    # define skip points
    if use_time_resolution:
        # time resolution
        num_target_pt = int((max_x - min_x+0.)/resolution)
    else:
        # maximum number
        num_target_pt = int(resolution)

    num_raw_points = i_stop - i_start
    if num_raw_points < num_target_pt * 2:
        pt_skip = 1
    else:
        pt_skip = int(num_raw_points/num_target_pt)

    plot_x = vec_x[i_start:i_stop:pt_skip]
    plot_y = vec_y[i_start:i_stop:pt_skip]

    # print 'Input vec_x = ', vec_x, 'vec_y = ', vec_y, i_start, i_stop, pt_skip, len(plot_x)

    return plot_x, plot_y
