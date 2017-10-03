# Zoo of graphics view widgets for "Live Data"
from mplgraphicsview import MplGraphicsView
from mplgraphicsview1d import MplGraphicsView1D


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
