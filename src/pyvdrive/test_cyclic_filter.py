import h5py
import numpy
from scipy.signal import argrelextrema


class Tester(object):
    
    def __init__(self):
        return
        

    def locate_cycle_boundaries(self, raw_ws_name, smoothed_ws_name, x_start, x_stop, cycle_local_max_lower_limit,
                                num_neighbors, trust_start_stop):


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
        # datatypeutility.check_float_variable('Starting time of cycles', x_start, (0, None))
        # datatypeutility.check_float_variable('Stopping time of cycles', x_stop, (0, None))
        if x_start >= x_stop:
            raise RuntimeError('Starting time {} cannot be equal to later than stopping time {}'
                               ''.format(x_start, x_stop))

        # get workspaces
        if False:
            raw_ws = mantid_helper.retrieve_workspace(raw_ws_name, True)
            smooth_ws = mantid_helper.retrieve_workspace(smoothed_ws_name, True)
        else:
            raw_ws = mtd[raw_ws_name]
            smooth_ws = mtd[smoothed_ws_name]

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

        # convert to vector: set the max_index_set back to local_maxima_indexes
        local_maxima_indexes = numpy.array(sorted(list(max_index_set)))   # this local_maxima_indexes is optimized from previous local_maxima_indexes
        maxima_times_vec = raw_vec_times[local_maxima_indexes]
        maxima_value_vec = raw_vec_value[local_maxima_indexes]

        # check
        avg_cycle_time, std_dev = check_statistic(maxima_times_vec, maxima_value_vec, 'info')

        # create a workspace
        CreateWorkspace(DataX=maxima_times_vec, DataY=maxima_value_vec, NSpec=1, OutputWorkspace='debug_maxima')

        if maxima_times_vec.shape[0] < 2:
            raise RuntimeError('Only found {} local maxima. Unable to proceed'.format(maxima_times_vec.shape[0]))

        # Step 3: find (real) minima by finding minimum between 2 neighboring local maxima
        local_minima_indexes = numpy.ndarray(shape=(maxima_value_vec.shape[0]+1, ), dtype='int64')
        for i_cycle in range(len(local_maxima_indexes) - 1):
            # locate the minima
            start_index_i = local_maxima_indexes[i_cycle]
            stop_index_i = local_maxima_indexes[i_cycle + 1]
            print ('# index: start = {}, stop = {}, # points = {}'.format(start_index_i, stop_index_i,
                                                                          stop_index_i - start_index_i))
            vec_x_i = raw_vec_times[start_index_i:stop_index_i]
            vec_y_i = raw_vec_value[start_index_i:stop_index_i]
            print ('[DEBUG] Cycle {}: Start @ {}, {}, Stop @ {}, {}'
                   ''.format(i_cycle, vec_x_i[0], vec_y_i[0], vec_x_i[-1], vec_y_i[-1]))

            # find local minima
            min_index_i = numpy.argmin(vec_y_i)
            print ('[DEBUG]  {}-th Local minimum: X = {}, Y = {} @ index = {} ... total index = {}'
                   ''.format(i_cycle + 1, vec_x_i[min_index_i], vec_y_i[min_index_i], min_index_i, start_index_i + min_index_i))

            # store the result
            local_minima_indexes[i_cycle + 1] = start_index_i + min_index_i
        # END-FOR

        # add the first and last local minimum as the cycle starts and ends at lower temperature
        cycle_indexes_size = local_minima_indexes[2] - local_minima_indexes[1]

        if trust_start_stop:
             start_cycle_index = numpy.searchsorted(raw_vec_times[0:local_maxima_indexes[0]], x_start, 'right')
             local_minima_indexes[0] = start_cycle_index
             
             end_cycle_index =  numpy.searchsorted(raw_vec_times[local_maxima_indexes[-1]:], x_stop, 'left')
             local_minima_indexes[-1] = end_cycle_index + local_maxima_indexes[-1]

        else:
            # use the 1st (i=1) local minimum time to determine the start (i=0)
            minimum_1_time = raw_vec_times[local_minima_indexes[1]]
            estimated_start_time = minimum_1_time - avg_cycle_time
            start_cycle_index = numpy.searchsorted(raw_vec_times[(local_minima_indexes[1] - int(1.01 * cycle_indexes_size)):local_maxima_indexes[0]], estimated_start_time, 'right')
            assert isinstance(start_cycle_index, int), '{}'.format(type(start_cycle_index))
            local_minima_indexes[0] = start_cycle_index + (local_minima_indexes[1] - int(1.01 * cycle_indexes_size))

            # use the last local minimum (i = -1)
            print (local_minima_indexes[-1], local_minima_indexes[-2])
            estimated_stop_time = raw_vec_times[local_minima_indexes[-2]] + avg_cycle_time
            print ('stop time: ', estimated_stop_time)
            end_cycle_index = numpy.searchsorted(raw_vec_times[local_maxima_indexes[-1]:(local_minima_indexes[-2] + int(1.01 * cycle_indexes_size))], estimated_stop_time, 'left')
            local_minima_indexes[-1] = end_cycle_index + local_maxima_indexes[-1]
        # END-IF
 
        # create a workspace
        minima_times_vec = raw_vec_times[local_minima_indexes]
        minima_value_vec = raw_vec_value[local_minima_indexes]
        CreateWorkspace(DataX=minima_times_vec, DataY=minima_value_vec, NSpec=1, OutputWorkspace='debug_minima')

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

        
    def pre_process_logs(self, vec_times, vec_log_value, num_neighbors):
        """ Pre-process sample logs for locating cycle boundaries
        :param vec_times:
        :param vec_log_value:
        :param num_neighbors:
        :return:
        """
        #datatypeutility.check_numpy_arrays('Vector for times and log values', [vec_times, vec_log_value], 1, True)
        #datatypeutility.check_int_variable('Number of neighbors to smooth', num_neighbors, (2, None))

        raw_ws_name = 'furnac2.raw'
        smoothed_ws_name = raw_ws_name.split('.')[0] + '.smoothed'
        CreateWorkspace(DataX=vec_times, DataY=vec_log_value, NSpec=1, OutputWorkspace=raw_ws_name)
        SmoothData(InputWorkspace=raw_ws_name, OutputWorkspace=smoothed_ws_name, NPoints=num_neighbors)

        return raw_ws_name, smoothed_ws_name
    
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

    def export_event_splitters(self, splitter_list, file_name):
        # check times
        time_dict = dict()

        # output buffer
        output = '# start time (s)    stop time (s)    target\n'
        for splitter in splitter_list:
            start_time, stop_time, target = splitter

            output += '%-15s %-15s %d\n' % ('{:.2f}'.format(start_time), '{:.2f}'.format(stop_time), target)

            if target not in time_dict:
                time_dict[target] = 0
            time_dict[target] += stop_time - start_time
        # END-FOR

        split_file = open(file_name, 'w')
        split_file.write(output)
        split_file.close()

        # output the time
        for target in sorted(time_dict.keys()):
            print ('{}:  {}  seconds'.format(target, time_dict[target]))

        return
    
    # TODO FIXME TONIGHT - This shall be moved to chop utility
    def set_cyclic_filters(self, raw_ws_name, local_minima_indexes, local_maxima_indexes, log_boundaries,
                           rising):

        if False:
            raw_ws = mantid_helper.retrieve_workspace(raw_ws_name, True)
        else:
            raw_ws = mtd[raw_ws_name]

        # prototype for create the event filters
        raw_vec_x = raw_ws.readX(0)
        raw_vec_y = raw_ws.readY(0)

        # skip for loop
        # rising edge

        splitter_list = list()   # start time, stop time, index
        num_log_sections = log_boundaries.shape[0] - 1
        splitter_index_list = list()

        for i_cycle in range(local_maxima_indexes.shape[0]):
            # each cycle
            i_start = local_minima_indexes[i_cycle]
            i_stop = local_maxima_indexes[i_cycle]

            # local splitter boundaries indexes
            splitter_index_vec = numpy.array([i_start, i_stop])


            log_0 = log_boundaries[0]
            pre_index = i_start + numpy.searchsorted(raw_vec_y[i_start:i_stop], log_0)
            splitter_index_list.append(pre_index)

            for i_log in range(num_log_sections):
                log_i = log_boundaries[i_log+1]
                # index_i = numpy.searchsorted(raw_vec_y[i_start:i_stop], log_i)
                # index_i += i_start
                index_i = i_start + numpy.searchsorted(raw_vec_y[i_start:i_stop], log_i)
                splitter_index_list.append(index_i)

                # create entry
                start_time_i = raw_vec_x[pre_index]
                stop_time_i = raw_vec_x[index_i]

                splitter_list.append([start_time_i, stop_time_i, i_log])

                # print (index_i, type(index_i))
                # splitter_index_vec = numpy.sort(splitter_index_vec)

                # update
                pre_index = index_i
            # END-FOR (single cycle)
        # END-IF

        # debug output
        if True:
            splitter_index_vec = numpy.array(splitter_index_list)
            splitter_times = raw_vec_x[splitter_index_vec]
            splitter_refs = raw_vec_y[splitter_index_vec]
            splitters = CreateWorkspace(DataX=splitter_times, DataY=splitter_refs, NSpec=1)
        # END-IF

        return splitter_list


    def test_load_process_(self):
        """
        Load log file written in HDF format as a test client method
        :return:
        """
        h5_name = 'furnace2c.h5'
        log_name = 'loadframe.furnace2'
        N = 5

        # get the sample log value from log file and create a workspace
        log_dict = self.load_sample_logs_h5(h5_name, log_name=log_name)
        vec_times, vec_value = log_dict['loadframe.furnace2']

        self.pre_process_logs(vec_times, vec_value, N)

        raw_ws_name = 'furnac2.raw'
        smoothed_ws_name = 'furnac2.smoothed'
        x_start = 1905   # seconds
        x_stop = 45079  # seconds 
        cycle_local_max_lower_limit = 400
        num_neighbors = N
        trust_start_stop = True
        minima_indexes, maxima_indexes = self.locate_cycle_boundaries(raw_ws_name, smoothed_ws_name, x_start, x_stop, cycle_local_max_lower_limit, num_neighbors, trust_start_stop)

        # generate filters
        log_boundaries = numpy.arange(100, 1100, 100)
        
        # export filters to ascii
        split_dict = self.set_cyclic_filters(raw_ws_name, local_minima_indexes=minima_indexes, local_maxima_indexes=maxima_indexes, log_boundaries=log_boundaries,
                           rising=True)
                           
        self.export_event_splitters(split_dict, 'slicer.txt')
        
        

tester = Tester()
tester.test_load_process_()