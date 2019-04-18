# Note: This script shall be executed inside MantidPlot after test_cyclic_filter
# separate log for events filter featuring temperature cooling section in the cycles
import numpy

cooling_splitters = list()   # item: start_t, stop_t, target_section, temperature min, temperature max

minima_ws = mtd['debug_minima']
maxima_ws = mtd['debug_maxima']

# determine starting point
if minima_ws.readX(0)[0] < maxima_ws.readX(0)[0]:
    min_start_index = 1
else:
    min_start_index = 0
# print min_start_index

min_temp = numpy.average(minima_ws.readY(0)[1:])
print ('Minimum temperature: {}'.format(min_temp))

# make a set of new vectors such that time_max[i] < time_min[i]
minima_times = minima_ws.readX(0)[min_start_index:]
maxima_times = maxima_ws.readX(0)[:]

# sample log value
vec_log_times = mtd['furnac2.raw'].readX(0)
vec_temperature = mtd['furnac2.raw'].readY(0)

# determine the range of each cycle in term of index on temperature log vector
section_boundary_list = list()  # = start time index (max), stop time index (min)
for index in range(min(len(minima_times), len(maxima_times))):

    print ('Maximum @ T = {}    --->   Minimum @ T = {}: delta T = {}'
           ''.format(maxima_times[index], minima_times[index], maxima_times[index] - minima_times[index]))

    # use search sorted to locate the min/max on the vec log: it may not be accurate
    index_list = numpy.searchsorted(vec_log_times, [maxima_times[index], minima_times[index]])

    print ('Try to locate: {}, {}   -->  Located to {}, {}'
           ''.format(maxima_times[index], minima_times[index],
                     vec_log_times[index_list[0]], vec_log_times[index_list[1]]))

    # correct
    found_max_index = index_list[0]
    if vec_log_times[found_max_index] - maxima_times[index] > maxima_times[index] - vec_log_times[found_max_index - 1]:
        found_max_index -= 1
        print ('Maximum is corrected to {}'.format(vec_log_times[found_max_index]))

    found_min_index = index_list[1]
    if vec_log_times[found_min_index] - minima_times[index] > minima_times[index] - vec_log_times[found_min_index - 1]:
        found_min_index -= 1
        print ('Minimum is corrected to {}'.format(vec_log_times[found_min_index]))

    print ('Section: {}'.format(vec_temperature[found_max_index:found_min_index+1]))

    section_boundary_list.append((found_max_index, found_min_index))

# END-FOR
    
# VZ determine: the boundaries
# boundaries = [96, 180, 360, 540, 720, 900]
b1 = range(100, 320, 10)
b2 = range(300, 900+60, 60)
boundaries = b1[:]
boundaries.extend(b2)
print (boundaries)
boundaries.sort(reverse=True)
print ('Final boundary (for cooling: {}'.format(boundaries))


out_str = ''
for max_time_index, min_time_index in section_boundary_list:

    # start_index, stop_index = index_list
    vec_log_value_i = vec_temperature[max_time_index:min_time_index + 1]
    print ('Temperature vec: {} ... {}'.format(vec_log_value_i[0], vec_log_value_i[-1]))
    
    # reverse the vector for searchsorted
    reversed_temp_i = vec_log_value_i[::-1]
    bound_index_list = numpy.searchsorted(reversed_temp_i, boundaries)
    # check again with left and right and correct
    for i, b_index_i in enumerate(bound_index_list):
        if boundaries[i] - reversed_temp_i[b_index_i-1] < reversed_temp_i[b_index_i] - boundaries[i]:
            bound_index_list[i] = b_index_i - 1  # closer to the value to the left
    # reverse back
    bound_index_list = list(reversed_temp_i.shape[0] - numpy.array(bound_index_list))  # reverse bound index again

    print (bound_index_list)
    # convert to splitters

    for i in range(len(bound_index_list)-1):
        b_i = bound_index_list[i]
        b_i_1 = bound_index_list[i+1]
        
        # quit loop if the next boundary point is out of loop
        if b_i_1 >= len(vec_log_value_i):
            continue
        
        time_start = vec_log_times[b_i + start_index]
        time_stop = vec_log_times[b_i_1 + start_index]
        print time_start, '\t\t', time_stop, '\t\t', i
        out_str += '{}  {}  {}\n'.format(time_start, time_stop, i)
    # ENDFOR

    print (out_str)    
        
    break
# ENDFOR
        
slicer_file = open('upslope_slicer', 'w')
slicer_file.write(out_str)
slicer_file.close()
