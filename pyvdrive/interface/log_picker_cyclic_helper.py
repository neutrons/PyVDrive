from pyvdrive.lib import datatypeutility
from gui import GuiUtility
import os
import numpy


class CyclicEventFilterSetupHelper(object):
    """ Class, used by PeakPickerWindow, contains methods to helper users to set up events filter
    against cyclic (straboscope) sample logs
    """
    def __init__(self, parent, ui_class):
        """

        :param parent:
        :param ui_class:
        """
        assert parent is not None, 'Parent class (Peak processing) cannot be None'
        assert ui_class is not None, 'UI class cannot be None'

        self._parent = parent
        self.ui = ui_class
        self._controller = self._parent.get_controller()

        self._curr_sample_log_dict = dict()  #  [log name] = vec times, vec value

        return

    # TODO - TODAY - TEST NEW METHOD
    def do_load_sample_log_file(self):
        """
        Load a sample log file other than EventNeXus file.
        The benefit of this operation is to avoid to loading unused logs
        :return:
        """
        # load a record file containing all the chopped data information
        log_file_name = GuiUtility.get_load_file_by_dialog(self, 'Sample log file',
                                                           self._controller.get_working_dir(),
                                                           'HDF5 (*.hdf5);;HDF5 (*.h5)')

        if log_file_name == '':
            # cancel the operation
            return

        # load
        from pyvdrive.lib import file_utilities
        self._curr_sample_log_dict = file_utilities.load_sample_logs_h5(log_file_name)

        return

    def find_cycle_boundaries(self):
        """
        Locate the boundaries between any adjacent cycles
        :return:
        """
        # locate the zero value in the 2nd derivative and use 2nd derivative to select the lower point
        numpy.where(vector > -0.001 and vector < 0.001 )
        self._curr_sample_log_deriv_1
        self._curr_sample_log_deriv_2

    def show_cycle_boundaries(self):
        """
        Show cycle boundaries on the
        :return:
        """
        # add 'red' circle to each selected/calculated cycle boundaries
        self.ui.graphicsView_main.addCycleBoundaries()

    def show_hide_derivatives(self, derivative_order, show):
        """
        show or hide n-th derivatives of the plots
        :param derivative_order:
        :param show:
        :return:
        """
        if show:
            self._derivative_line[derivative_order] = self.ui.graphicsView_main.plot_derivative(vec_times,
                                                                                                vec_derivative_i)
        elif self._derivative_line[derivative_order] is None:
            pass
        else:
            self.ui.graphicsView_main.remove_derivative(self._derivative_line[derivative_order])

        return

    def update_cycle_boundaries(self):
        """
        Update the boundaries inside the cycle
        :return:
        """
        boundary_point_list = self.ui.graphicsView_main.get_cycle_boundaries()
        self.ui.tableWidget_boundaries.set_values(boundary_point_list)

        return

    def show_n_th_boundary(self, n):
        """
        Show n-th boundary by adding an indicator
        :return:
        """
        boundary_points = self.ui.graphicsView_main.get_cycle_boundaries()
        datatypeutility.check_int_variable('N-th boundaries points', n, (0, len(boundary_points)))

        n_th_time = boundary_points[n]

        return n_th_time

    # TODO FIXME TONIGHT - This shall be moved to chop utility
    def set_cyclic_filter(self, vec_times, vec_value, cyclic_boundary_vec, cycle_range, min_value, max_value, value_step):
        """
        This is a prototype algorithm to set up the event filters for cyclic data.
        It will leave the performance issue to be solved in future
        :param cyclic_boundary_vec:
        :param cycle_range:
        :param min_value:
        :param max_value:
        :param value_step:
        :return:
        """
        import time

        def check_interval_against_cycle_direction(cycle_boundary_vec, splitter_index_tuple):
            return False

        def convert_to_time(splitter_index_tuples):
            """
            convert from sample log entry indexes to relative time (to run start)
            :param splitter_index_tuples:
            :return:
            """
            return None

        t_start = time.time()

        boundary_index = 0   # assuming that boundary starts from the smallest log value in the cycle

        ramping_up_filters = list()
        ramping_down_filters = list()

        # num_intervals = (max_value - min_value) / value_step
        # if abs(float(int(num_intervals)) - num_intervals) < 1E-4:
        #     num_intervals = int(num_intervals)
        # else:
        #     num_intervals = int(num_intervals) + 1
        interval_vec = numpy.arange(min_value, max_value, value_step)

        slicer_list = list()

        # go through the
        boundary_index = 0
        curr_boundary_min = interval_vec[0]
        curr_boundary_max = interval_vec[1]
        for index in range(vec_times.shape[0]):
            if vec_value[index] < curr_boundary_max and vec_value[index] >= curr_boundary_min:
                # within the current range
                pass
            else:
                # out of the boundary
                new_index = numpy.searchsorted(interval_vec, vec_value[index])
                curr_slicer_indexes = splitter_start_index, index
                is_ramping_up = check_interval_against_cycle_direction(boundary_index, curr_slicer_indexes)
                if is_ramping_up:
                    ramping_up_filters.append(curr_slicer_indexes)
                else:
                    ramping_down_filters.append(curr_slicer_indexes)
            # END-IF-ELSE
        # END-FOR

        ramping_up_filters = convert_to_time(ramping_up_filters)
        ramping_down_filters = convert_to_time(ramping_down_filters)

        t_stop = time.time()

        print ('[INFO] (Prototype of) Cyclic log event splitters setup: # entries = {}'
               ', time used = {} seconds'.format(cyclic_boundary_vec.shape, t_stop - t_start))

        return ramping_up_filters, ramping_down_filters

    # TODO - TOMORROW - It is assumed that the boundaries of cycles are given by array indexes, then a binary search
    # TODO              on log value with specified range can be applied such that
    def set_slicer_cyclic_logs(self):

        for i_half_cycle in range(2 * num_cycles):
            # up ramp
            if i_half_cycle / 2 == 0:
                start_i_index = local_minimum_index
                stop_i_index = local_maximum_index
            else:
                start_i_index = local_maximum_index
                stop_i_index = local_minimum_index
            # even one: ramping up
            for i_interval in range(num_intervals):
                # search for the boundary
                boundary_index_i = numpy.searchsorted(vec_values[start_i_index: stop_i_index], boundary_index_i)
                slicer_dict[i_interval].append([boundary_index_i_prev, boundary_index_i])

        return