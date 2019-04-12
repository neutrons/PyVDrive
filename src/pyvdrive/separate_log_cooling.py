# separate log for filtering
import numpy

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
# boundaries = [96, 180, 360, 540, 720, 900]
b1 = range(100, 320, 10)
b2 = range(300, 900+60, 60)
boundaries = b1[:]
boundaries.extend(b2)
print (boundaries)
boundaries.sort(reverse=True)
print (boundaries)


out_str = ''
for index in range(0, len(maxima_times)-1):
    # get the range of one cooling cycle
    print maxima_times[index],  '    ----    ', minima_times[index+1], '  ..... deta T = ',  minima_times[index + 1] - maxima_times[index]
    index_list = numpy.searchsorted(vec_log_times, [maxima_times[index], minima_times[index+1]]) 
    print ('{} - {}: {}'.format(index_list[0], index_list[1], index_list[1] - index_list[0]))
    
    start_index, stop_index = index_list
    vec_temp_i = vec_temperature[start_index:stop_index+1]
    print ('Temerature vec: {} ... {}'.format(vec_temp_i[0], vec_temp_i[-1]))
    
    # reverse the vector
    reversed_temp_i = vec_temp_i[::-1]
    bound_index_list = numpy.searchsorted(reversed_temp_i, boundaries)
    print (bound_index_list)
    
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
    """    
    for i, b_i in enumerate(bound_index_list):
        # process
        if b_i > 0 and b_i < len(vec_temp_i) and abs(vec_temp_i[b_i-1] - boundaries[i]) < abs(vec_temp_i[b_i] -  boundaries[i]):
            bound_index_list[i] -= 1
    """
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
        print time_start, '\t\t', time_stop, '\t\t', i
        out_str += '{}  {}  {}\n'.format(time_start, time_stop, i)
    # ENDFOR

    print (out_str)    
        
    break
# ENDFOR
        
slicer_file = open('upslope_slicer', 'w')
slicer_file.write(out_str)
slicer_file.close()
