# Goal: Find peaks are not aligned with others in focused TOF and dSpacing
import mantid
from mantid.simpleapi import CloneWorkspace, Load, ConvertUnits, AlignAndFocusPowder, LoadDiffCal, Rebin
from mantid.api import AnalysisDataService as mtd

# Clone group workspace
if 'diamond' not in mtd:
    Load(Filename='/SNS/VULCAN/IPTS-19576/nexus/VULCAN_160457.nxs.h5', OutputWorkspace='diamond')
LoadDiffCal(InputWorkspace='diamond',
            Filename='/home/wzz/Vulcan-Calibration/2017_8_11_CAL/VULCAN_calibrate_2017_08_17_27bank.h5',
            WorkspaceName='vulcan_27')
group_ws = CloneWorkspace(InputWorkspace='vulcan_27_group', OutputWorkspace='vulcan_debug_group')

# original 27 banks focused data
vulcan_l1 = 40.
vulcan_l2_list = [2.] * 27
vulcan_2theta_list = [270.]*9
vulcan_2theta_list.extend([90.]*9)
vulcan_2theta_list.extend([150.]*9)
vulcan_azimulth_list = [0] * 27

# Get range of wd index for group=4
ws_index_list = list()
for iws in range(group_ws.getNumberHistograms()):  # : if 3.9 < group_ws.readX(iws)[0] < 4.1]
    print group_ws.readX(iws)[0]
    if 3.9 < group_ws.readY(iws)[0] < 4.1:
        ws_index_list.append(iws)

ws_index_list.sort()
print ws_index_list[0], ws_index_list[-1]
group4_start_index = ws_index_list[0]
group4_stop_index = ws_index_list[-1]  # included

# Nail down
midindex = (1436 + 1078) / 2

""" Step 1  Nail down to lower """
for iws in range(1078, 1200):
    group_ws.dataY(iws)[0] = 28
for iws in range(1200, midindex):
    group_ws.dataY(iws)[0] = 29
vulcan_l2_list.extend([2., 2.])
vulcan_2theta_list.extend([270., 270.])
vulcan_azimulth_list.extend([0., 0])

spectra_list = range(1, 29)

# step2 : more aggressive
# for iws in range(1078, midindex):
#     group_ws.dataY(iws)[0] = 28
#     
#     
#     
# for iws in range(1085, 1092):
#     group_ws.dataY(iws)[0] = 29
# for iws in range(1092, 1099):
#     group_ws.dataY(iws)[0] = 30
# for iws in range(1099, 2006):
#     group_ws.dataY(iws)[0] = 31
# for iws in range(2006, ):
#     group_ws.dataY(iws)[0] = 32

# apply the new group workspace to diamond data
AlignAndFocusPowder(InputWorkspace='raw_diamond', OutputWorkspace='focus2',
                    GroupingWorkspace='vulcan_debug_group', CalibrationWorkspace='vulcan_27_cal',
                    MaskWorkspace='vulcan_27_mask', Params='-0.001', DMin='0.5', DMax='5',
                    Spectra=spec_list,
                    L1=vulcan_l1,
                    L2=vulcan_l2_list,
                    twotheta=vulcan_2theta_list,
                    azimuthal=vulcan_azimulth_list)
ConvertUnits(InputWorkspace='diamond', OutputWorkspace='diamond', Target='dSpacing', ConvertFromPointData=False)
Rebin(InputWorkspace='diamond', OutputWorkspace='diamond', Params='0.5,-0.001,2', FullBinsOnly=True)

