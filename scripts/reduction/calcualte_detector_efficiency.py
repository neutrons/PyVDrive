# Use Mantid algorithm Integrate to calculate the vanadium efficiency
# NOTE: This is meant to run with MantidPlot
#
# Overview:
# 1. Base TOF range is (10000, 30000)
# 2. Shift (proportionally) the TOF range by L2/2 of each pixel
# 3. Integrate counts of each pixels between shifted TOF range
# 4. Normalize the counts and reverse to be the weights
#
import numpy
import h5py
import datetime

van_run = 156473   # 161069: bad  # vulcan_158562
van_ws = 'vanadium_{0}'.format(van_run)

if not mtd.doesExist('vanadium'):
    Load(Filename='/SNS/VULCAN/IPTS-19653/nexus/VULCAN_{0}.nxs.h5'.format(van_run), OutputWorkspace=van_ws)

# uniform integration
if not mtd.doesExist('van_uniform_sum'):
    Integration(InputWorkspace=van_ws, OutputWorkspace='van_uniform_sum', RangeLower=10000, RangeUpper=30000)

# integration with fine tune
van_ws = mtd['vanadium']
start_index = 0
stop_index = van_ws.getNumberHistograms() - 1
print ('Range of index: [{0}, {1}]'.format(start_index, stop_index))

# TOF ranges
RangeLowerList = [10000] * van_ws.getNumberHistograms()
RangeUpperList = [30000] * van_ws.getNumberHistograms()

for iws in range(van_ws.getNumberHistograms()):
    l2_i_pos = van_ws.getDetector(iws).getPos()
    l2_i = l2_i_pos.norm()
    RangeLowerList[iws] = RangeLowerList[iws] * l2_i * 0.5
    RangeUpperList[iws] = RangeUpperList[iws] * l2_i * 0.5
    
print ('Range of lowest TOF among all detectors: {0}, {1}'.format(min(RangeLowerList), max(RangeLowerList)))
print ('Range of highest TOF among all detectors: {0}, {1}'.format(min(RangeUpperList), max(RangeUpperList)))

# get the minimum and maximum TOF


# Need to cut off all the data
params = '{0}, -0.001, {1}'.format(10000, max(RangeUpperList))
print (params)

Rebin(InputWorkspace='vanadium',
      Params='{0},-0.001,{1}'.format(10000, max(RangeUpperList)),
      FullBinsOnly=True,
      OutputWorkspace='vanadium')

# Integration takes Workspace2D only (it counts intensities but not number of events)
ConvertToMatrixWorkspace(InputWorkspace='vanadium', OutputWorkspace='vanadium2d')
# Integrate counts for each pixels
Integration(InputWorkspace='vanadium2d', OutputWorkspace='van_tuned_sum',
            RangeLowerList=RangeLowerList,
            RangeUpperList=RangeUpperList)

# convert integrated counts to vectors
weight_ws = mtd['van_tuned_sum']
num_spec = weight_ws.getNumberHistograms()

pid_vec = numpy.ndarray(shape=(num_spec,), dtype='int64')
weight_vec = numpy.ndarray(shape=(num_spec,), dtype='float')

for iws in range(num_spec):
    pid_vec[iws] = weight_ws.getDetector(iws).getID()
    weight_vec[iws] = weight_ws.readY(iws)[0]

# normalize and reverse
weight_vec = numpy.max(weight_vec) / weight_vec

# write to HDF5 file
eff_name = 'vulcan_eff_{0}.hdf5'.format(van_run)
eff_file = h5py.File(eff_name, 'w')

# point to the default data to be plotted
eff_file.attrs[u'default'] = u'entry'
# give the HDF5 root some more attributes
eff_file.attrs[u'file_name'] = eff_name
eff_file.attrs[u'file_time'] = '{0}'.format(datetime.datetime.now())
eff_file.attrs[u'instrument'] = u'SNS VULCAN BL-7'

# create the NXentry group
nx_entry = eff_file.create_group(u'entry')
nx_entry.attrs[u'NX_class'] = u'NXentry'
nx_entry.attrs[u'default'] = u'detector_efficiency'
nx_entry.create_dataset(u'title', data=u'Detector Efficiency')

# create the NXentry group
nx_data = nx_entry.create_group(u'detector_efficiency')
nx_data.attrs[u'NX_class'] = u'NXdata'
nx_data.attrs[u'signal'] = u'weight'    # Y axis of default plot
nx_data.attrs[u'axes'] = u'pid'         # X axis of default plot
nx_data.attrs[u'mr_indices'] = [0,]     # use "mr" as the first dimension of I00


# X axis data
ds = nx_data.create_dataset(u'pid', data=pid_vec)
ds.attrs[u'units'] = u''
ds.attrs[u'long_name'] = u'Pixel ID'    # suggested X axis plot label

# Y axis data
ds = nx_data.create_dataset(u'I00', data=weight_vec)
ds.attrs[u'units'] = u''
ds.attrs[u'long_name'] = u'Detector Efficiency Factor'    # suggested Y axis plot label

eff_file.close()   # be CERTAIN to close the file
