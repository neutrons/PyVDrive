import mantid
from mantid.simpleapi import *

IPTS = 22752
Run  = 172335
Peaks = [(1.92, 0.03),]
Bank = 1   # 1: west   2: east   3: high angle

spec_range = {1: (0, 3234),
              2: (3234, 6468),
              3: (6468, 24900)}

# Load data
LoadEventNexus(Filename='/SNS/VULCAN/IPTS-{}/nexus/VULCAN_{}.nxs.h5'.format(IPTS, Run), OutputWorkspace='si')
# Load calibration
LoadDiffCal(InputWorkspace='si', Filename='/SNS/VULCAN/shared/CALIBRATION/2019_1_20/VULCAN_calibrate_2019_01_21.h5', WorkspaceName='vulcan_')
# Align detectors (DIFC) and convert to dSpacing
AlignDetectors(InputWorkspace='si', OutputWorkspace='si', CalibrationWorkspace='vulcan__cal')
# Rebin
Rebin(InputWorkspace='si', OutputWorkspace='si', Params='0.5,-0.001,3.5')

# Fit peaks and output results
for peak_position, peak_width in Peaks:
    tag = '{}'.format(peak_position)
    tag = tag.strip().replace('.', '')
    FitPeaks(InputWorkspace='si',
             StartWorkspaceIndex=spec_range[Bank][0], StopWorkspaceIndex=spec_range[Bank][1],
             PeakCenters=peak_position,
             FitWindowBoundaryList='{}, {}'.format(peak_position - peak_width, peak_positon + peak_width),
             OutputWorkspace='Peaks_{}'.format(tag),
             FittedPeaksWorkspace='Fitted{}'.format(tag),
             OutputPeakParametersWorkspace='Params{}'.format(tag))
    Transpose(InputWorkspace='Peaks_{}'.format(tag), OutputWorkspace='Peaks_{}'.format(tag))

    # export peak center and sigma
    
sigma = Params092.column('Sigma')
Params092.column('PeakCentre')
ws_index = Params092.column('wsindex')

type(ws_index)
Out[12]: list

for i in range(3, 6):
    wbuf = 
  File "<ipython-input-13-8e64b8da0a43>", line 2
    wbuf =
           ^
SyntaxError: invalid syntax


for i in range(3, 6):
    wbuf = '{}  {}\n'.format(ws_index[i], sigma[i])
    

print (wbuf)
5  0.00136057820748 
