import numpy as np

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

        # register dictionaries
        self._sizeRegister = dict()

        # extra title message
        self._titleMessage = ''

        return

    def plot_sample_log(self, vec_x, vec_y, sample_log_name):
        """ Purpose: plot sample log

        Guarantee: canvas is replot
        :param vec_x
        :param vec_y
        :param sample_log_name:
        :return:
        """
        # check
        assert isinstance(vec_x, np.ndarray), 'VecX must be a numpy array but not %s.' \
                                              '' % vec_x.__class__.__name__
        assert isinstance(vec_y, np.ndarray), 'VecY must be a numpy array but not %s.' \
                                              '' % vec_y.__class__.__name__
        assert isinstance(sample_log_name, str)

        # set label
        try:
            the_label = '%s Y (%f, %f)' % (sample_log_name, min(vec_y), max(vec_y))
        except TypeError as type_err:
            err_msg = 'Unable to generate log with %s and %s: %s' % (
                str(min(vec_y)), str(max(vec_y)), str(type_err))
            raise TypeError(err_msg)

        # add plot and register
        plot_id = self.add_plot_1d(vec_x, vec_y, label=the_label, marker='.', color='blue')
        self._sizeRegister[plot_id] = (min(vec_x), max(vec_x), min(vec_y), max(vec_y))

        # auto resize
        self.resize_canvas(margin=0.05)

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

    def reset(self):
        """
        Reset canvas
        :return:
        """
        # dictionary
        self._sizeRegister.clear()

        # clear all lines
        self.clear_all_lines()

        return

# END-DEFINITION

