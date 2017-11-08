# Zoo of graphics view widgets for "Live Data"
import numpy

from mplgraphicsview import MplGraphicsView
from mplgraphicsview1d import MplGraphicsView1D
from mplgraphicsview2d import MplGraphicsView2D


class GeneralPurpose1DView(MplGraphicsView1D):
    """

    """
    def __init__(self, parent):
        """
        blabla
        :param parent:
        """
        super(GeneralPurpose1DView, self).__init__(parent, 1, 1)

        return


class Live2DView(MplGraphicsView2D):
    """
    canvas for visualization of multiple reduced data in 2D
    """
    def __init__(self, parent):
        """
        blabla
        :param parent:
        """
        super(Live2DView, self).__init__(parent)

        return

    def plot_contour(self, data_set_dict):
        """
        blabla
        :param data_set_dict: dictionary such that
        :return:
        """
        # Check inputs
        # blabla

        # TODO/NOW/TODO - doc and check

        # construct
        x_list = sorted(data_set_dict.keys())
        vec_x = data_set_dict[x_list[0]][0]
        vec_y = numpy.array(x_list)
        size_x = len(vec_x)

        # build mesh and matrix y
        # grid_x, grid_y = numpy.meshgrid(vec_x, vec_y)
        # print '[DB...BAT] original size: {0}, {1} and grid shape = {2}'.format(len(vec_x), len(vec_y), grid_x.shape)
        # original size: 2257, 2 and grid shape = (2, 2257)
        # matrix_y = numpy.ndarray(grid_x.shape, dtype='float')

        grid_shape = len(vec_y), len(vec_x)
        matrix_y = numpy.ndarray(grid_shape, dtype='float')
        for index in vec_y:
            # vector X
            vec_x_i = data_set_dict[index][0]
            if len(vec_x_i) != size_x:
                # TODO/TODO/labor - better message
                raise RuntimeError('blabla')

            # vector Y: each row will have the value of a pattern
            matrix_y[index:] = data_set_dict[index][1]  #
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
