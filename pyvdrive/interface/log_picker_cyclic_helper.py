from pyvdrive.lib import datatypeutility
from pyvdrive.lib import file_utilities
from gui import GuiUtility
from mantid.simpleapi import CreateWorkspace
from pyvdrive.lib import mantid_helper
from numpy import argrelextrema
import os
import numpy
import h5py

"""
Note: Mantid workspace is used to store the data because smoothing algorithm is used
"""


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
        self._curr_sample_log_dict = self.load_sample_logs_h5(log_file_name)
        #  file_utilities.load_sample_logs_h5(log_file_name)

        return


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

    def load_sample_logs_h5(self, log_h5_name, log_name=None):
        """
        Load standard sample log (TimeSeriesProperty) from an HDF file
        Note: this is paired with save_sample_logs_h5
        :param log_h5_name:
        :param log_name: specified log name to load.  If None, then load all the sample logs
        :return: dictionary: d[log name] = vec_times, vec_values  of numpy arrays
        """

        def is_sample_log(log_entry_name):
            return log_h5[log_entry_name].has_attribute('sample log')

        def read_log(log_entry_name):
            vec_times = log_h5[log_entry_name]['time'].value
            vec_value = log_h5[log_entry_name]['value'].value
            return vec_times, vec_value

        # datatypeutility.check_file_name(log_h5_name, True, False, False, 'PyVDRive HDF5 sample log file')

        log_h5 = h5py.File(log_h5_name, 'r')

        sample_log_dict = dict()
        if log_name is None:
            for log_name in log_h5.keys():
                if not is_sample_log(log_name):
                    continue
                sample_log_dict[log_name] = read_log(log_name)
        else:
            sample_log_dict[log_name] = read_log(log_name)

        return sample_log_dict

    def pre_process_logs(self, vec_times, vec_log_value, num_neighbors):
        """ Pre-process sample logs for locating cycle boundaries
        :param vec_times:
        :param vec_log_value:
        :param num_neighbors:
        :return:
        """
        datatypeutility.check_numpy_arrays('Vector for times and log values', [vec_times, vec_log_value], 1, True)
        datatypeutility.check_int_variable('Number of neighbors to smooth', num_neighbors, (2, None))

        raw_ws_name = 'furnac2.raw'
        smoothed_ws_name = raw_ws_name.split('.')[0] + '.smoothed'
        CreateWorkspace(DataX=vec_times, DataY=vec_log_value, NSpec=1, OutputWorkspace=raw_ws_name)
        SmoothNeighbor(InputWorkspace=raw_ws_name, OutputWorkspace=smoothed_ws_name, N=num_neighbors)

        return raw_ws_name, smoothed_ws_name

    def locate_cycle_boundaries(self, raw_ws_name, smoothed_ws_name, x_start, x_stop, cycle_local_max_lower_limit,
                                num_neighbors):


        def check_statistic(max_x_vector, max_y_vector, level):
            diff_max_x_vec = max_x_vector[1:] - max_x_vector[:-1]
            std_dev = numpy.std(diff_max_x_vec)
            avg_cycle_time = numpy.average(diff_max_x_vec)
            false_indexes = numpy.where(diff_max_x_vec < numpy.std(diff_max_x_vec))[0]

            msg = 'Cycle time = {} +/- {}\nFalse local maxima: {}, {}' \
                  ''.format(avg_cycle_time, std_dev, max_x_vector[false_indexes], max_y_vector[false_indexes])
            print ('[{}]: {}'.format(level.upper(), msg))

            return avg_cycle_time, std_dev

        # User input from observation
        # Requirement: precisely pin point the start of first cycle and stop of last cycle
        # x_start = 1713
        # x_stop = 45073
        # cycle_max_lower_limit = 400

        # check inputs
        datatypeutility.check_float_variable('Starting time of cycles', x_start, (0, None))
        datatypeutility.check_float_variable('Stopping time of cycles', x_stop, (0, None))
        if x_start >= x_stop:
            raise RuntimeError('Starting time {} cannot be equal to later than stopping time {}'
                               ''.format(x_start, x_stop))

        # get workspaces
        raw_ws = mantid_helper.retrieve_workspace(raw_ws_name, True)
        smooth_ws = mantid_helper.retrieve_workspace(smoothed_ws_name, True)

        # use smoothed workspace to locate maxima first
        vec_x = smooth_ws.readX(0)
        vec_y = smooth_ws.readY(0)

        raw_vec_times = raw_ws.readX(0)
        raw_vec_value = raw_ws.readY(0)

        # determine start and stop indexes
        start_index = numpy.searchsorted(vec_x, x_start)
        stop_index = numpy.searchsorted(vec_x, x_stop, 'right')
        print ('[INFO] Start X = {}, Y = {}, Index = {}'.format(vec_x[start_index], vec_y[start_index], start_index))
        print ('[INFO] Stap  X = {}, Y = {}, Index = {}'.format(vec_x[stop_index], vec_y[stop_index], stop_index))

        # Step 1: use smoothed data to find local maxima: use 'argrelextrema' to find local maxima
        roi_vec_x = vec_x[start_index:stop_index]
        roi_vec_y = vec_y[start_index:stop_index]

        roi_maxima_indexes = argrelextrema(roi_vec_y, numpy.greater)
        roi_maxima_indexes = roi_maxima_indexes[0]  # get to list
        print ('[DEBUG] maximum indexes (in ROI arrays): {}'.format(roi_maxima_indexes))

        # convert to the raw
        local_maxima_indexes = roi_maxima_indexes + start_index

        # there are a lot of local maxima from signal noise: filter out the small values
        max_y_vector = raw_vec_value[local_maxima_indexes]   # log values of local maxima
        y_indexes = numpy.where(max_y_vector > cycle_local_max_lower_limit)  # indexes for max Y vector
        local_maxima_indexes = local_maxima_indexes[y_indexes]
        maxima_times_vec = raw_vec_times[local_maxima_indexes]   # times for local maxima
        # equivalent to: max_x_vector = max_x_vector[y_indexes]
        maxima_value_vec = raw_vec_value[local_maxima_indexes]   # log values of local maxima
        # equivalent to: max_y_vector = max_y_vector[y_indexes]
        # print ('Filtered indexes: {}'.format(max_index_vector))

        check_statistic(maxima_times_vec, maxima_value_vec, level='debug')

        # Step 2: map from smoothed data to raw data (real maxima)
        max_index_set = set()
        for max_index_i in local_maxima_indexes:
            # search the nearby N = 5 points
            i_start = max_index_i - num_neighbors
            i_stop = max_index_i + num_neighbors
            max_index_i = numpy.argmax(raw_vec_value[i_start:i_stop])
            max_index_set.add(max_index_i + i_start)
        # END-FOR

        # convert to vector
        max_index_vector = numpy.array(sorted(list(max_index_set)))
        maxima_times_vec = raw_vec_times[max_index_vector]
        maxima_value_vec = raw_vec_value[max_index_vector]

        # check
        avg_cycle_time, std_dev = check_statistic(maxima_times_vec, maxima_value_vec, 'info')

        # create a workspace
        CreateWorkspace(DataX=maxima_times_vec, DataY=maxima_value_vec, NSpec=1, OutputWorkspace='debug_maxima')

        if maxima_times_vec.shape[0] < 2:
            raise RuntimeError('Only found {} local maxima. Unable to proceed'.format(maxima_times_vec.shape[0]))

        # Step 3: find (real) minima by finding minimum between 2 neighboring local maxima
        local_minima_indexes = numpy.ndarray(shape=(maxima_value_vec.shape[0]+2, ), dtype='int64')
        for i_cycle in range(len(max_index_vector) - 1):
            # locate the minima
            start_index_i = max_index_vector[i_cycle]
            stop_index_i = max_index_vector[i_cycle + 1]
            print ('# index: start = {}, stop = {}, # points = {}'.format(start_index_i, stop_index_i,
                                                                          stop_index_i - start_index_i))
            vec_x_i = raw_vec_times[start_index_i:stop_index_i]
            vec_y_i = raw_vec_value[start_index_i:stop_index_i]
            print ('[DEBUG] Cycle {}: Start @ {}, {}, Stop @ {}, {}'
                   ''.format(i_cycle, vec_x_i[0], vec_y_i[0], vec_x_i[-1], vec_y_i[-1]))

            # find local minima
            min_index_i = numpy.argmin(vec_y_i)
            print ('[DEBUG]    Local minimum: X = {}, Y = {} @ index = {}'
                   ''.format(vec_x_i[min_index_i], vec_y_i[min_index_i], min_index_i))

            # store the result
            local_minima_indexes[i_cycle + 1] = start_index_i + min_index_i
        # END-FOR

        # add the first and last local minimum as the cycle starts and ends at lower temperature
        # use the 1st (i=1) local minimum time to determine the start (i=0)
        minimum_1_time = raw_vec_times[local_minima_indexes[1]]
        estimated_start_time = minimum_1_time - avg_cycle_time
        cycle_indexes_size = local_minima_indexes[2] - local_minima_indexes[1]

        start_cycle_index = numpy.searchsorted(raw_vec_times[(local_minima_indexes[1] - int(1.5 * cycle_indexes_size)):local_maxima_indexes[0]], estimated_start_time, 'right')
        local_minima_indexes[0] = start_index[0][0] + (local_minima_indexes[1] - int(1.5 * cycle_indexes_size))

        estimated_stop_time = raw_vec_times[local_minima_indexes[-2]] + avg_cycle_time
        end_cycle_index = numpy.searchsorted(raw_vec_times[local_maxima_indexes[-1]:(local_minima_indexes[-2] + int(1.5 * cycle_indexes_size))], estimated_stop_time, 'left')
        local_minima_indexes[-1] = end_cycle_index

        # export to HDF5
        if False:
            local_minima_indexes += start_index
            max_index_vector += start_index
            cycle_file = h5py.File('furnace2_cycles.h5', 'w')
            log_group = cycle_file.create_group('furnace2')
            log_group.create_dataset('minima', data=local_minima_indexes)
            log_group.create_dataset('maxima', data=max_index_vector)
            log_group['logname'] = 'furnace2'
            cycle_file.close()
        # END-IF

        return local_minima_indexes, local_maxima_indexes


    def set_event_splitters(self, raw_ws_name, local_minima_indexes, local_maxima_indexes):

        raw_ws = mantid_helper.retrieve_workspace(raw_ws_name, True)

        # prototype for create the event filters
        raw_vec_x = raw_ws.readX(0)
        raw_vec_y = raw_ws.readY(0)

        log_boundaries = np.arange(100, 1000, 100)


        # skip for loop
        # rising edge

        for i_cycle in range(local_maxima_indexes.shape[0]):
            # i_cycle = 2
            i_start = local_minima_indexes[i_cycle]
            i_stop = local_maxima_indexes[i_cycle]

            # local splitter boundaries indexes
            splitter_index_vec = numpy.array([i_start, i_stop])

            for log_i in log_boundaries:
                index_i = numpy.searchsorted(raw_vec_y[i_start:i_stop], log_i)
                index_i += i_start
                splitter_index_vec = numpy.append(splitter_index_vec, index_i)
                print (index_i, type(index_i))
                splitter_index_vec = numpy.sort(splitter_index_vec)

            splitter_times = raw_vec_x[splitter_index_vec]
            splitter_refs = raw_vec_y[splitter_index_vec]
        # END-IF

        # debug output
        splitters = CreateWorkspace(DataX=splitter_times, DataY=splitter_refs, NSpec=1)

        return

    def test_load_process_(self):
        """
        Load log file written in HDF format as a test client method
        :return:
        """
        h5_name = 'furnace2c.h5'
        log_name = 'loadframe.furnace2'

        # get the sample log value from log file and create a workspace
        log_dict = self.load_sample_logs_h5(h5_name, log_name=log_name)
        vec_times, vec_value = log_dict['loadframe.furnace2']

        self.pre_process_logs

        self.locate_cycle_boundaries(vec_times, vec_value)


        # smooth


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
