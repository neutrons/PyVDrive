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

upslope_splitters = list()

minima_ws = mtd['debug_minima']
maxima_ws = mtd['debug_maxima']

if minima_ws.readX(0)[0] < maxima_ws.readX(0)[0]:
    min_start_index = 0
else:
    min_start_index = 1
    
print min_start_index

min_temp = numpy.average(minima_ws.readY(0)[1:])
print (min_temp)

minima_times = minima_ws.readX(0)
maxima_times = maxima_ws.readX(0)
vec_log_times = mtd['furnac2.raw'].readX(0)
vec_temperature = mtd['furnac2.raw'].readY(0)

for index in range(0, len(minima_times)-1):
    # print minima_times[index], '    ----    ', maxima_times[index], '  ..... deta T = ', maxima_times[index] - minima_times[index]
    index_list = numpy.searchsorted(vec_log_times, [minima_times[index], maxima_times[index]])
    # print ('{} - {}: {}'.format(index_list[0], index_list[1], index_list[1] - index_list[0]))
    print (vec_temperature[ index_list[0]:  index_list[1] ])
    
# VZ determine:
boundaries = [96, 180, 360, 540, 720, 900]

out_str = ''
for index in range(0, len(minima_times)-1):
    # print minima_times[index], '    ----    ', maxima_times[index], '  ..... deta T = ', maxima_times[index] - minima_times[index]
    index_list = numpy.searchsorted(vec_log_times, [minima_times[index], maxima_times[index]])
    # print ('{} - {}: {}'.format(index_list[0], index_list[1], index_list[1] - index_list[0]))
    
    start_index, stop_index = index_list
    vec_temp_i = vec_temperature[start_index:stop_index+1]
    
    bound_index_list = numpy.searchsorted(vec_temp_i, boundaries)
    """
    for i, b_i in enumerate(bound_index_list):
        print b_i
        if b_i < len(vec_temp_i):
            print vec_temp_i[b_i],
        else:
           print 'max Y = {}'.format(vec_temp_i[-1]) 
           continue
        if b_i > 0 and abs(vec_temp_i[b_i-1] - boundaries[i]) < abs(vec_temp_i[b_i] -  boundaries[i]):
            print '  ---> ', vec_temp_i[b_i-1]
        else:
            print
    """
        
    for i, b_i in enumerate(bound_index_list):
        # process
        if b_i > 0 and b_i < len(vec_temp_i) and abs(vec_temp_i[b_i-1] - boundaries[i]) < abs(vec_temp_i[b_i] -  boundaries[i]):
            bound_index_list[i] -= 1
    print bound_index_list
    
    # convert to splitters

    for i in range(len(bound_index_list)-1):
        b_i = bound_index_list[i]
        b_i_1 = bound_index_list[i+1]
        
        # quit loop if the next boundary point is out of loop
        if b_i_1 >= len(vec_temp_i):
            continue
        
        time_start = vec_log_times[b_i + start_index]
        time_stop = vec_log_times[b_i_1 + start_index]
        print time_start, 't\t', time_stop, '\t\t', i
        out_str += '{}  {}  {}\n'.format(time_start, time_stop, i)
        
slicer_file = open('upslope_slicer', 'w')
slicer_file.write(out_str)
slicer_file.close()
