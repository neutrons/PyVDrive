# TODO/ISSUE/55 - Docs..
import numpy as np
import mplgraphicsview


class GeneralRunView(mplgraphicsview.MplGraphicsView):
    """

    """
    def __init__(self, parent):
        """

        :param parent:
        """
        super(GeneralRunView, self).__init__(parent)

        # class state variables
        self._plotDimension = 1
        self._plotType = None

        return

    def plot_2d_contour(self, run_number_list, data_set_list):
        """

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
