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

    # TODO - TONIGHT - From prototype to software
    def clean_load_log_h5(self):
        import h5py

        # TODO - TODAY - TEST : with new workflow test on cyclic data
        def load_sample_logs_h5(log_h5_name, log_name=None):
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

        h5_name = 'furnace2c.h5'
        log_dict = load_sample_logs_h5(h5_name, log_name='loadframe.furnace2')

        vec_times, vec_value = log_dict['loadframe.furnace2']

        # import mantid
        # rom mantid.simpleapi import *

        CreateWorkspace(DataX=vec_times, DataY=vec_value, NSpec=1, OutputWorkspace='furnac2.raw')

        print (vec_times)
        vec_times[0]

        import numpy as np

        gradient = np.gradient(vec_value, vec_times)
        print (gradient)

        deriv = (vec_value[1:] - vec_value[:-1]) / (vec_times[1:] - vec_times[:-1])
        deriv2 = (deriv[1:] - deriv[:-1]) / ((vec_times[1:] - vec_times[:-1])[:-1])

        from matplotlib import pyplot as plt

        plt.plot(vec_times, vec_value)
        plt.plot(vec_times[:-1], deriv)
        plt.plot(vec_times[:-2], deriv2)
        plt.show()

        # Study and convertToWaterfall
        from scipy.signal import argrelextrema
        import numpy as np

        x = mtd['furnac2.raw.SmoothData'].readY(0)
        x = x[1000:5000]
        print (mtd['furnac2.raw.SmoothData'].readX(0)[1000])
        print (mtd['furnac2.raw.SmoothData'].readX(0)[5000])

        # for local maxima
        maxes = argrelextrema(x, np.greater)
        maxes = maxes[0]
        print ('maximum indexes: {}'.format(maxes))

        vec_x = mtd['furnac2.raw.SmoothData'].readX(0)[1000:5000][maxes]
        vec_y = x[maxes]

        # filter out the small values
        y_indexes = np.where(vec_y > 400)
        vec_x = vec_x[y_indexes]
        vec_y = vec_y[y_indexes]
        filter_indexes = maxes[y_indexes]
        print (filter_indexes)

        max_points = CreateWorkspace(DataX=vec_x, DataY=vec_y, NSpec=1)

        vec_raw_x = mtd['furnac2.raw.SmoothData'].readX(0)[1000:5000]
        vec_raw_y = mtd['furnac2.raw.SmoothData'].readY(0)[1000:5000]

        slot1 = filter_indexes[0], filter_indexes[1]
        print (slot1)

        min_index = np.argmin(vec_raw_y[slot1[0]: slot1[1]])
        print (min_index)

        raise
        # for local minima
        mins = argrelextrema(x, np.less)
        mins = mins[0]

        vec_min_y = x[mins]
        vec_min_x = mtd['furnac2.raw.SmoothData'].readX(0)[1000:5000][mins]
        min_points = CreateWorkspace(DataX=vec_min_x, DataY=vec_min_y, NSpec=1)

        vec_s_x = mtd['furnac2.raw.SmoothData'].readX(0)[1000:5000]
        vec_s_y = mtd['furnac2.raw.SmoothData'].readY(0)[1000:5000]
        deriv_s_x = (vec_s_y[1:] - vec_s_y[:-1]) / (vec_s_x[1:] - vec_s_x[:-1])
        print (deriv_s_x[mins])
        print (max(deriv_s_x[mins]))

    # TODO - TONIGHT - From prototype to software
    def find_boundaries_sort(self):
        from scipy.signal import argrelextrema
        import numpy as np
        import h5py

        # User input from observation
        # Requirement: precisely pin point the start of first cycle and stop of last cycle
        x_start = 1713
        x_stop = 45073
        cycle_max_lower_limit = 400

        # use moderate smoothed neightbour data
        """
        x = mtd['furnac2.raw.SmoothData'].readY(0)
        """

        vec_x = mtd['furnac2.raw.SmoothData'].readX(0)
        vec_y = mtd['furnac2.raw.SmoothData'].readY(0)

        # numpy.searchsorted(a, v, side='left', sorter=None)[source]
        start_index = np.searchsorted(vec_x, x_start)
        stop_index = np.searchsorted(vec_x, x_stop, 'right')
        print ('[INFO] Start X = {}, Y = {}, Index = {}'.format(vec_x[start_index], vec_y[start_index], start_index))
        print ('[INFO] Stap  X = {}, Y = {}, Index = {}'.format(vec_x[stop_index], vec_y[stop_index], stop_index))

        """
        x = x[1000:5000]
        print (mtd['furnac2.raw.SmoothData'].readX(0)[1000])
        print (mtd['furnac2.raw.SmoothData'].readX(0)[5000])
        """

        # for local maxima on smoothed data
        roi_vec_x = vec_x[start_index:stop_index]
        roi_vec_y = vec_y[start_index:stop_index]

        maxes = argrelextrema(roi_vec_y, np.greater)
        maxes = maxes[0]  # get to list
        print ('[DEBUG] maximum indexes (in ROI arrays): {}'.format(maxes))

        """
        vec_x =  mtd['furnac2.raw.SmoothData'].readX(0)[1000:5000][maxes]
        vec_y = x[maxes]
        """
        max_x_vector = roi_vec_x[maxes]
        max_y_vector = roi_vec_y[maxes]

        # filter out the small values
        y_indexes = np.where(max_y_vector > cycle_max_lower_limit)
        max_index_vector = maxes[y_indexes]
        max_x_vector = max_x_vector[y_indexes]
        max_y_vector = max_y_vector[y_indexes]
        print ('Filtered indexes: {}'.format(max_index_vector))

        # check 1
        diff_max_x_vec = max_x_vector[1:] - max_x_vector[:-1]
        print (np.std(diff_max_x_vec))
        print (np.where(diff_max_x_vec < np.std(diff_max_x_vec)))
        indexes = np.where(diff_max_x_vec < np.std(diff_max_x_vec))[0]
        print (max_x_vector[indexes], max_y_vector[indexes])
        print ('\n------------------------------\n')

        # filtering method 2: mapping to original data
        raw_roi_vec_x = mtd['furnac2.raw'].readX(0)[start_index:stop_index]
        raw_roi_vec_y = mtd['furnac2.raw'].readY(0)[start_index:stop_index]

        max_index_set = set()
        N = 5
        for max_index_i in max_index_vector:
            # search the nearby N = 5 points
            i_start = max_index_i - N
            i_stop = max_index_i + N
            max_index_i = np.argmax(raw_roi_vec_y[i_start:i_stop])
            max_index_set.add(max_index_i + i_start)
        # convert to vector
        max_index_vector = np.array(sorted(list(max_index_set)))
        max_x_vector = raw_roi_vec_x[max_index_vector]
        max_y_vector = raw_roi_vec_y[max_index_vector]
        print ('Filtered indexes: {}'.format(max_index_vector))

        # check 2
        diff_max_x_vec = max_x_vector[1:] - max_x_vector[:-1]
        print (np.std(diff_max_x_vec))
        print (np.where(diff_max_x_vec < np.std(diff_max_x_vec)))
        indexes = np.where(diff_max_x_vec < np.std(diff_max_x_vec))[0]
        print (max_x_vector[indexes], max_y_vector[indexes])

        max_points = CreateWorkspace(DataX=max_x_vector, DataY=max_y_vector, NSpec=1)

        local_minima_indexes = list()
        # locate the minima
        for i_cycle in range(len(max_index_vector) - 1):
            start_index_i = max_index_vector[i_cycle]
            stop_index_i = max_index_vector[i_cycle + 1]
            print ('# index: start = {}, stop = {}, # points = {}'.format(start_index_i, stop_index_i,
                                                                          stop_index_i - start_index_i))
            vec_x_i = roi_vec_x[start_index_i:stop_index_i]
            vec_y_i = roi_vec_y[start_index_i:stop_index_i]
            print (
            '[DEBUG] Cycle {}: Start @ {}, {}, Stop @ {}, {}'.format(i_cycle, vec_x_i[0], vec_y_i[0], vec_x_i[-1],
                                                                     vec_y_i[-1]))

            # find local minima
            min_index_i = np.argmin(vec_y_i)
            print (
            '[DEBUG]    Local minimum: X = {}, Y = {} @ index = {}'.format(vec_x_i[min_index_i], vec_y_i[min_index_i],
                                                                           min_index_i))

            # store the result
            local_minima_indexes.append(start_index_i + min_index_i)
        # END-FOR

        # create from index
        min_x_vector = roi_vec_x[local_minima_indexes]
        min_y_vector = roi_vec_y[local_minima_indexes]
        min_points = CreateWorkspace(DataX=min_x_vector, DataY=min_y_vector, NSpec=1)

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
        else:
            # convert to original x range
            local_minima_indexes += start_index
            max_index_vector += start_index

        # TODO -TONIGHT - Deperately need a good algorithm to
        local_maxima_indexes = max_index_vector
        local_minima_indexes = numpy.insert(local_minima_indexes, 0, 5)
        local_minima_indexes = numpy.append(local_minima_indexes, max_index_vector[-1] + 100)

        # prototype for create the event filters
        raw_vec_x = mtd['furnac2.raw'].readX(0)
        raw_vec_y = mtd['furnac2.raw'].readY(0)

        # skip for loop
        # rising edge
        i_cycle = 2
        i_start = local_minima_indexes[i_cycle]
        i_stop = local_maxima_indexes[i_cycle]

        splitter_index_vec = np.array([i_start, i_stop])

        log_boundaries = np.arange(100, 1000, 100)
        for log_i in log_boundaries:
            index_i = np.searchsorted(raw_vec_y[i_start:i_stop], log_i)
            index_i += i_start
            splitter_index_vec = np.append(splitter_index_vec, index_i)
            print (index_i, type(index_i))
        splitter_index_vec = np.sort(splitter_index_vec)

        splitter_times = raw_vec_x[splitter_index_vec]
        splitter_refs = raw_vec_y[splitter_index_vec]

        splitters = CreateWorkspace(DataX=splitter_times, DataY=splitter_refs, NSpec=1)

        """
        raise
        # for local minima
        mins = argrelextrema(x, np.less)
        mins = mins[0]

        vec_min_y = x[mins]
        vec_min_x =  mtd['furnac2.raw.SmoothData'].readX(0)[1000:5000][mins]
        min_points = CreateWorkspace(DataX=vec_min_x, DataY=vec_min_y, NSpec=1)

        vec_s_x =  mtd['furnac2.raw.SmoothData'].readX(0)[1000:5000]
        vec_s_y =  mtd['furnac2.raw.SmoothData'].readY(0)[1000:5000]
        deriv_s_x = (vec_s_y[1:] - vec_s_y[:-1]) / (vec_s_x[1:] - vec_s_x[:-1])
        print (deriv_s_x[mins])
        print (max(deriv_s_x[mins]))
        """

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
