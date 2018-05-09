# Chop data to 5 seconds and reduce to GSAS
# Test case: run = 160989, duration = 0.69 hour

import time
t0 = time.time()
import mantid
from mantid.simpleapi import Load, GenerateEventsFilter, FilterEvents, LoadDiffCal, AlignAndFocusPowder, Rebin, AlignDetectors, ConvertUnits
from mantid.simpleapi import DiffractionFocussing

# chop data
ipts = 18522
run_number = 160560


# event_file_name = '/SNS/VULCAN/IPTS-13924/nexus/VULCAN_160989.nxs.h5'
# event_file_name = '/SNS/VULCAN/IPTS-{0}/nexus/VULCAN_{1}.nxs.h5'.format(ipts, run_number)
event_file_name = '/SNS/VULCAN/IPTS-19577/nexus/VULCAN_155771.nxs.h5'

Load(Filename=event_file_name, OutputWorkspace='ws')
LoadDiffCal(InputWorkspace='ws',
        Filename='/SNS/VULCAN/shared/CALIBRATION/2018_4_11_CAL/VULCAN_calibrate_2018_04_12.h5', WorkspaceName='vulcan')
AlignDetectors(InputWorkspace='ws', OutputWorkspace='ws', CalibrationWorkspace='vulcan_cal')

t1 = time.time()

time_bin = 300
time_bin = 60
GenerateEventsFilter(InputWorkspace='ws', OutputWorkspace='MatrixSlicer', InformationWorkspace='MatrixInfoTable',
                     FastLog=True, TimeInterval=time_bin)
result = FilterEvents(InputWorkspace='ws', SplitterWorkspace='MatrixSlicer', InformationWorkspace='MatrixInfoTable', 
                      OutputWorkspaceBaseName='FiveMin',
                      FilterByPulseTime=False, GroupWorkspaces=True, OutputWorkspaceIndexedFrom1=True, SplitSampleLogs=True)

print ('There are {0} returned objects from FilterEvents.'.format(len(result)))
output_names = None
for r in result:
    if isinstance(r, int):
        print r
    elif isinstance(r, list):
        output_names = r
    else:
        continue
        # print r.name(), type(r)
t2 = time.time()

# print ('The chopped workspaces: {0}'.format(output_names))

# Load calibration
ws_name_0 = output_names[0]

# Now start to use multi-threading
import threading

def reduce_data(ws_name_list):
    for ws_name in ws_name_list:
        ConvertUnits(InputWorkspace=ws_name, OutputWorkspace=ws_name, Target='dSpacing')
        DiffractionFocussing(InputWorkspace=ws_name, OutputWorkspace=ws_name, GroupingWorkspace='vulcan_group')
        ConvertUnits(InputWorkspace=ws_name, OutputWorkspace=ws_name, Target='TOF', ConvertFromPointData=False)

num_outputs = len(output_names)
num_threads = 1
half_num = int(num_outputs/num_threads)

thread_pool = dict()
for thread_id in range(num_threads):
    start = thread_id * half_num
    end = min(start + half_num, num_outputs)
    thread_pool[thread_id] = threading.Thread(target=reduce_data, args=(output_names[start:end],))
    thread_pool[thread_id].start()
    print ('thread {0}: [{1}: {2})'.format(thread_id, start, end))

for thread_id in range(num_threads):
    thread_pool[thread_id].join()

# t1 = threading.Thread(target=reduce_data, args=(output_names[:half_num],))
# t2 = threading.Thread(target=reduce_data, args=(output_names[half_num:],))
# t1.start()
# t2.start()
# t1.join()
# t2.join()


# # # reduce
# for ws_name in output_names:
#     ConvertUnits(InputWorkspace=ws_name, OutputWorkspace=ws_name, Target='dSpacing')
#     DiffractionFocussing(InputWorkspace=ws_name, OutputWorkspace=ws_name, GroupingWorkspace='vulcan_group')
#     ConvertUnits(InputWorkspace=ws_name, OutputWorkspace=ws_name, Target='TOF', ConvertFromPointData=False)
#     # Rebin(InputWorkspace=ws_name, OutputWorkspace=ws_name, Params='5000,-0.001,50000', FullBinsOnly=True)

tf = time.time()

print ('{0}: Runtime = {1}   Total outputworkspace = {2}'.format(event_file_name, tf-t0, len(output_names)))
print ('Details for thread = {3}:\n\tLoading  = {0}\n\tChopping = {1}\n\tFocusing = {2}'.format(t1-t0, t2-t1, tf-t2, num_threads))
