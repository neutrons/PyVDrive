# Clone group
CloneWorkspace(InputWorkspace='vulcan_27_group', OutputWorkspace='vulcan_debug_group')

# Get range of wd index for group4
group_ws = mtd['vulcan_debug_group']
ws_index_list = list()
for iws in range(group_ws.getNumberHistograms()):  # : if 3.9 < group_ws.readX(iws)[0] < 4.1]
    print group_ws.readX(iws)[0]
    if 3.9 < group_ws.readY(iws)[0] and group_ws.readY(iws)[0] < 4.1:
        ws_index_list.append(iws)

ws_index_list.sort()
print ws_index_list[0], ws_index_list[-1]

# Nail down
midindex = (1436 + 1078) / 2

""" Step 1  Nail down to lower
for iws in range(1078, 1200):
    group_ws.dataY(iws)[0] = 28
for iws in range(1200, midindex):
    group_ws.dataY(iws)[0] = 29
"""
# step2 : more aggressive
for iws in range(1078, 1085):
    group_ws.dataY(iws)[0] = 28
for iws in range(1085, 1092):
    group_ws.dataY(iws)[0] = 29
for iws in range(1092, 1099):
    group_ws.dataY(iws)[0] = 30
for iws in range(1099, 2006):
    group_ws.dataY(iws)[0] = 31
for iws in range(2006, midindex):
    group_ws.dataY(iws)[0] = 32



#-------------------------------------------
Load(Filename='/SNS/VULCAN/IPTS-19576/nexus/VULCAN_160457.nxs.h5', OutputWorkspace='diamond')
ConvertUnits(InputWorkspace='diamond', OutputWorkspace='diamond', Target='dSpacing', ConvertFromPointData=False)
Rebin(InputWorkspace='diamond', OutputWorkspace='diamond', Params='0.5,-0.001,2', FullBinsOnly=True)
LoadDiffCal(InputWorkspace='diamond', Filename='/home/wzz/Vulcan-Calibration/2017_8_11_CAL/VULCAN_calibrate_2017_08_17_27bank.h5', WorkspaceName='vulcan_27')
Load(Filename='/SNS/VULCAN/IPTS-19576/nexus/VULCAN_160457.nxs.h5', OutputWorkspace='raw_diamond')
AlignAndFocusPowder(InputWorkspace='raw_diamond', OutputWorkspace='focus', GroupingWorkspace='vulcan_27_group', CalibrationWorkspace='vulcan_27_cal', MaskWorkspace='vulcan_27_mask', Params='-0.001', DMin='0.5', DMax='5')
CloneWorkspace(InputWorkspace='vulcan_27_group', OutputWorkspace='vulcan_debug_group')
AlignAndFocusPowder(InputWorkspace='raw_diamond', OutputWorkspace='focus2', GroupingWorkspace='vulcan_debug_group', CalibrationWorkspace='vulcan_27_cal', MaskWorkspace='vulcan_27_mask', Params='-0.001', DMin='0.5', DMax='5')
CloneWorkspace(InputWorkspace='vulcan_27_group', OutputWorkspace='vulcan_debug_group')
AlignAndFocusPowder(InputWorkspace='raw_diamond', OutputWorkspace='focus2', GroupingWorkspace='vulcan_debug_group', CalibrationWorkspace='vulcan_27_cal', MaskWorkspace='vulcan_27_mask', Params='-0.001', DMin='0.5', DMax='5')
CloneWorkspace(InputWorkspace='vulcan_27_group', OutputWorkspace='vulcan_debug_group')
AlignAndFocusPowder(InputWorkspace='raw_diamond', OutputWorkspace='focus2', GroupingWorkspace='vulcan_debug_group', CalibrationWorkspace='vulcan_27_cal', MaskWorkspace='vulcan_27_mask', Params='-0.001', DMin='0.5', DMax='5')
CloneWorkspace(InputWorkspace='vulcan_27_group', OutputWorkspace='vulcan_debug_group')
AlignAndFocusPowder(InputWorkspace='raw_diamond', OutputWorkspace='focus2', GroupingWorkspace='vulcan_debug_group', CalibrationWorkspace='vulcan_27_cal', MaskWorkspace='vulcan_27_mask', Params='-0.001', DMin='0.5', DMax='5')
CloneWorkspace(InputWorkspace='vulcan_27_group', OutputWorkspace='vulcan_debug_group')
AlignAndFocusPowder(InputWorkspace='raw_diamond', OutputWorkspace='focus2', GroupingWorkspace='vulcan_debug_group', CalibrationWorkspace='vulcan_27_cal', MaskWorkspace='vulcan_27_mask', Params='-0.001', DMin='0.5', DMax='5')
CloneWorkspace(InputWorkspace='vulcan_27_group', OutputWorkspace='vulcan_debug_group')
AlignAndFocusPowder(InputWorkspace='raw_diamond', OutputWorkspace='focus2', GroupingWorkspace='vulcan_debug_group', CalibrationWorkspace='vulcan_27_cal', MaskWorkspace='vulcan_27_mask', Params='-0.001', DMin='0.5', DMax='5')
