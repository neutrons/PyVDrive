# Note: This script shall be executed inside MantidPlot after test_cyclic_filter
# separate log for events filter featuring temperature rising section in the cycles
import numpy

# TODO - TONIGHT 0 - List of tasks for Hazah
# TODO - ... ...   - 1. Reformat this like separating for cooling
# TODO - ... ...   - 2. Rename to ..._heating.py
# TODO - ... ..    - 3. Detailed debugging information for how to determine the start/stop for each segments
# TODO - ... ...   -    including (1) theoretical start/stop value vs algorithm-found-log start/stop
# TODO - ... ...   -    (2) cycle number
# TODO - ... ...   - 4. Can define the range of cycles
# TODO - ... ...   - 5. Output file for (1) over-all and (2) each individual segment
# TODO - ... ...   - 6. Do statistic on each target workspace average and standard deviation
# TODO - ... ...   - 7. Modify cooling.py accordingly
# TODO - ... ...   - 8. Output file including information such as the sample log it is sliced from


def search_sorted_nearest(vector, values):
    index_list = numpy.searchsorted(vector, values, side='left', sorter=None)
    for i, index_i in enumerate(index_list):
        if index_i == 0:
            pass  # already out of left boundary
        elif index_i == vector.shape[0]:
            pass  # already out of right boundary
        elif values[i] - vector[index_i-1] < vector[index_i] - values[i]:
            # v_i is closer to left value
            index_list[i] = index_i - 1
    # END-FOR

    return index_list


# set up data
minima_ws = mtd['debug_minima']
maxima_ws = mtd['debug_maxima']
minima_times = minima_ws.readX(0)
minima_vec = minima_ws.readY(0)
maxima_times = maxima_ws.readX(0)
maxima_vec = maxima_ws.readY(0)

furnace_log_ws = mtd['furnac2.raw']
vec_log_times = furnace_log_ws.readX(0)
vec_temperature = furnace_log_ws.readY(0)

# determine the starting point
if minima_times[0] < maxima_times[0]:
    min_start_index = 0
else:
    min_start_index = 1
    minima_times = minima_times[1:]
    minima_vec = minima_vec[1:]
    maxima_times = maxima_times[1:]
    maxima_vec = maxima_vec[1:]

print '[INFO] starting index = {}'.format(min_start_index)

# information of minimum
print ('[INFO] Furnace temperature minima = {} +/- {}'.format(numpy.average(minima_vec), numpy.std(minima_vec)))

# map from minima/maxima to cycles: information only this time
# after first round, this can be skipped
for i_cycle in range(0, len(minima_times)-1):  # minima always ends with a false-minimum (continue to cool down)

    minimum_time_i = minima_times[i_cycle]
    maximum_times_i = maxima_times[i_cycle]

    cycle_indexes = search_sorted_nearest(vec_log_times, [minimum_time_i, maximum_times_i])
    print ('Cycle {}: {}'.format(i_cycle, vec_temperature[cycle_indexes[0]:cycle_indexes[1]]))
# END-FOR
    
# TODO-NOTE: user determine!
boundaries = [96, 180, 360, 540, 720, 900]
start_cycle_number = 0
stop_cycle_number = 19
phase_index = 1

out_str = ''   # output file format
heating_splitters = list()  # item: start_t, stop_t, target_section, temperature min, temperature max

for i_cycle in range(start_cycle_number, stop_cycle_number+1):
    print ('[CHECK] Cycle = {}'.format(i_cycle))

    minimum_time_i = minima_times[i_cycle]
    maximum_times_i = maxima_times[i_cycle]

    cycle_indexes = search_sorted_nearest(vec_log_times, [minimum_time_i, maximum_times_i])

    # get the sub section of furnace temperature log
    start_index, stop_index = cycle_indexes
    vec_temp_i = vec_temperature[start_index:stop_index+1]

    print ('\tTemperature: {}'.format(vec_temp_i))

    # search boundaries
    bound_index_list = search_sorted_nearest(vec_temp_i, boundaries)  # numpy.searchsorted(vec_temp_i, boundaries)
    
    # create splitters
    for i_splitter in range(len(bound_index_list)-1):
        b_i = bound_index_list[i_splitter]
        b_i_1 = bound_index_list[i_splitter+1]

        print ('[CHECK]\t\ts[{}]: Index [{}, {})'.format(i_splitter, b_i, b_i_1))
        
        # quit loop if the next boundary point is out of loop
        if b_i_1 >= len(vec_temp_i):
            print ('[WARNING] Boundary index for stop (= {}) is out of boundary'.format(b_i_1))
            break

        # get time and value
        time_start = vec_log_times[b_i + start_index]
        time_stop = vec_log_times[b_i_1 + start_index]
        value_start = vec_temperature[b_i + start_index]
        value_stop = vec_temperature[b_i_1 + start_index]

        out_str += '{}  {}  {}  {}  {}  {}\n' \
                   ''.format(time_start, time_stop, i_cycle, value_start, value_stop, time_stop - time_start)

        print ('[CHECK]\t\t   Time: {}  {}, Value: {},  {}, Delta T = {}\n'
               ''.format(time_start, time_stop, value_start, value_stop, time_stop - time_start))
    # END-FOR
# END-FOR

slicer_file = open('heating_slicers_section_{}'.format(phase_index), 'w')
slicer_file.write(out_str)
slicer_file.close()
