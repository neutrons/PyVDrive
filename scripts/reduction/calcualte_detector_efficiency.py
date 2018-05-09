# Use Mantid algorithm Integrate to calculate the vanadium efficiency
run = 156473 # 161069: bad  # vulcan_158562

if not mtd.doesExist('vanadium'):
    Load(Filename='vulcan_{0}'.format(run), OutputWorkspace='vanadium')

# uniform integration
if not mtd.doesExist('van_uniform_sum'):
    Integration(InputWorkspace='vanadium', OutputWorkspace='van_uniform_sum', RangeLower=10000, RangeUpper=30000)

# integration with fine tune
van_ws = mtd['vanadium']
start_index = 0
stop_index = van_ws.getNumberHistograms() - 1
print (start_index, stop_index)

RangeLowerList = [10000] * van_ws.getNumberHistograms()
RangeUpperList = [30000] * van_ws.getNumberHistograms()

for iws in range(van_ws.getNumberHistograms()):
    l2_i_pos = van_ws.getDetector(iws).getPos()
    l2_i = l2_i_pos.norm()
    RangeLowerList[iws] = RangeLowerList[iws] * l2_i * 0.5
    RangeUpperList[iws] = RangeUpperList[iws] * l2_i * 0.5
    
print (min(RangeLowerList), max(RangeLowerList))
print (min(RangeUpperList), max(RangeUpperList))

params = '{0}, -0.001, {1}'.format(10000, max(RangeUpperList))
print (params)

Rebin(InputWorkspace='vanadium', Params='{0},-0.001,{1}'.format(10000, max(RangeUpperList)),FullBinsOnly=True, OutputWorkspace='vanadium')
ConvertToMatrixWorkspace(InputWorkspace='vanadium', OutputWorkspace='vanadium2d')

Integration(InputWorkspace='vanadium2d', OutputWorkspace='van_tuned_sum',
                   RangeLowerList=RangeLowerList,
                   RangeUpperList=RangeUpperList)

