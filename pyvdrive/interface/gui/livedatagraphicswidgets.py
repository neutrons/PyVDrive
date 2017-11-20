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
        super(GeneralPurpose1DView, self).__init__(parent, 1, 1)

        return

    # TODO/NOW/89 - Implement!
    def plot_sample_log(self, blabla):
        """
        Requirements
        1. compare with currently plotted sample to determine whether it is to remove current plot and plot a new
           line or update current line
        2. determine color style and etc.
        :param blabla:
        :return:
        """
        pass

    # TODO/NOW/89 - Implement!
    def plot_peak_parameters(self, blabla):
        """
        Requirements
        1. compare with currently plotted sample to determine whether it is to remove current plot and plot a new
           line or update current line
        2. determine color style and etc.
        :param blabla:
        :return:
        """
        pass


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
