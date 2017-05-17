import numpy as np
import mplgraphicsview


class GeneralRunView(mplgraphicsview.MplGraphicsView):
    """

    """
    ColorList = ['black', 'red', 'blue', 'green', 'yellow']
    def __init__(self, parent):
        """
        An extension to the MplGraphicsView for plotting reduced run
        :param parent:
        """
        super(GeneralRunView, self).__init__(parent)

        # class state variables
        self._plotDimension = 1
        self._plotType = None

        # dictionary and etc for current line IDs
        # self._linesDict = dict()  : don't know how to deal with it!
        self._onCanvasIDList = list()
        self._currLineID = None

        # mode for diffraction (d) or sample logs (s)
        self._dataMode = None

        # a record for min and max X and Y
        self._maxX = None
        self._maxY = None

        return

    def plot_diffraction_data(self, vec_xy_set, unit, over_plot, run_id=None, chop_tag=None):
        """
        plot diffraction data with proper
        :param vec_xy_set:
        :param unit:
        :param over_plot:
        :param run_id:
        :param chop_tag:
        :return:
        """
        # data mode blabla
        if self._dataMode != 'd':
            self.reset_1d_plots()
            self._dataMode = 'd'

        # get vectors
        vec_x = vec_xy_set[0]
        vec_y = vec_xy_set[1]

        # process the current image
        if not over_plot:
            self.clear_all_lines()
            self._onCanvasIDList = list()

        # FIXME/TODO/ISSUE/TODAY - Use cyclic color
        self._currLineID = self.plot_1d_data(vec_x, vec_y, unit, label=chop_tag, line_key=chop_tag,
                                             title=run_id, line_color='blue')
        self._onCanvasIDList.append(self._currLineID)

        # re-scale
        self.auto_rescale()

        return

    def plot_sample_data(self, vec_times, vec_value, workspace_key, sample_name):
        """

        :param vec_times:
        :param vec_value:
        :param workspace_key:
        :param sample_name:
        :return:
        """
        # data mode blabla
        if self._dataMode != 's':
            self.reset_1d_plots()
            self._dataMode = 's'

        # plot
        auto_color = GeneralRunView.ColorList[len(self._onCanvasIDList) % len(GeneralRunView.ColorList)]

        self._currLineID = self.plot_1d_data(vec_times, vec_value, 'second', label=workspace_key, line_key=None,
                                             title=sample_name, line_color=auto_color)
        self._onCanvasIDList.append(self._currLineID)

        # re-scale
        self.auto_rescale()
        self.setXYLimit(xmin=0.)

        return

    def plot_1d_data(self, vec_x, vec_y, x_unit, label, line_key=None, title='', line_color='red'):
        """
        plot a 1-D data set
        :param vec_x:
        :param vec_y:
        :param x_unit:
        :param label:
        :param line_key:
        :param title:
        :param line_color
        :return:
        """
        line_id = self.add_plot_1d(vec_x=vec_x, vec_y=vec_y, label=label,
                                   x_label=x_unit, marker='.', color=line_color)
        print '[DB...BAT] New line ID = {0}.'.format(line_id)
        self.set_title(title)

        # register
        # self._linesDict[line_key] = line_id

        # record statistics
        if self._maxX is None or vec_x[-1] > self._maxX:
            self._maxX = vec_x[-1]

        if self._maxY is None or np.max(vec_y) > self._maxY:
            self._maxY = np.max(vec_y)

        return line_id

    def plot_2d_contour(self, run_number_list, data_set_list):
        """
        plot 2D contour figure
        :param run_number_list:
        :param data_set_list:
        :return:
        """
        # check
        size_set = set()
        for data_set in data_set_list:
            vec_x, vec_y = data_set
            assert len(vec_x) == len(vec_y), 'Size of vector X (%d) and vector Y (%d) must be same!' % (len(vec_x), len(vec_y))
            size_set.add(len(vec_x))
        # END-FOR
        assert len(size_set) == 1, 'All the reduced data must have equal sizes but not %s.' % str(size_set)
        vec_x = data_set_list[0][0]

        # build mesh
        grid_x, grid_y = np.meshgrid(vec_x, run_number_list)

        matrix_y = np.ndarray(grid_x.shape, dtype='float')
        for i in range(len(run_number_list)):
            matrix_y[:i] = data_set_list[i][1]

        n = len(run_number_list)
        vec_y = np.ndarray(shape=(n,), dtype='int')
        for i in range(n):
            vec_y[i] = run_number_list[i]

        self.canvas().add_contour_plot(vec_x, np.array(run_number_list), matrix_y)

        return

    def set_dimension_type(self, target_dim, target_type):
        """
        set dimension and type
        :param target_dim:
        :param target_type:
        :return:
        """
        # check
        assert isinstance(target_dim, int) and 1 <= target_dim <= 3, 'Target dimension must be an integer between 1 and 3.'

        # clear current canvas
        self.clear_canvas()

        # set the target dimension
        self._plotDimension = target_dim
        self._plotType = target_type

        return

    def reset_1d_plots(self):
        """
        reset all 1D plots
        :return:
        """
        # clear all lines
        self.clear_all_lines()

        # clear dictionary
        # self._linesDict.clear()
        self._currLineID = None
        self._onCanvasIDList = list()

        # reset X and Y
        self._maxX = None
        self._maxY = None

        return
