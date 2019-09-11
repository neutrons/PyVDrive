# This is a prototype to test masking

# ---------------------> Templates

# Background
LoadDiffCal(InstrumentName='vulcan', Filename='/SNS/VULCAN/shared/CALIBRATION/2019_1_20/VULCAN_calibrate_2019_01_21.h5', WorkspaceName='vulcan')
LoadEventNexus(Filename='/SNS/VULCAN/IPTS-22753/nexus/VULCAN_172362.nxs.h5', OutputWorkspace='Background_Raw')
AlignDetectors(InputWorkspace='Background_Raw', OutputWorkspace='Background_Raw', CalibrationWorkspace='vulcan_cal')
ConvertUnits(InputWorkspace='Background_Raw', OutputWorkspace='Background_Raw', Target='Wavelength', AlignBins=True)
Rebin(InputWorkspace='Background_Raw', OutputWorkspace='Background_Raw', Params='0.1,-0.05,5', FullBinsOnly=True, IgnoreBinErrors=True)
ConvertUnits(InputWorkspace='Background_Raw', OutputWorkspace='Background_Raw', Target='Wavelength', AlignBins=True)
Rebin(InputWorkspace='Background_Raw', OutputWorkspace='Background_Raw', Params='0.3,0.7,1,2,3,2,5', FullBinsOnly=True, IgnoreBinErrors=True)

# Vanadium
LoadDiffCal(InstrumentName='vulcan', Filename='/SNS/VULCAN/shared/CALIBRATION/2019_1_20/VULCAN_calibrate_2019_01_21.h5', WorkspaceName='vulcan')
LoadEventNexus(Filename='/SNS/VULCAN/IPTS-22752/nexus/VULCAN_172254.nxs.h5', OutputWorkspace='Vanadium_Raw')
AlignDetectors(InputWorkspace='Vanadium_Raw', OutputWorkspace='Vanadium_Raw', CalibrationWorkspace='vulcan_cal')
ConvertUnits(InputWorkspace='Vanadium_Raw', OutputWorkspace='Vanadium_Raw', Target='Wavelength', AlignBins=True)
Rebin(InputWorkspace='Vanadium_Raw', OutputWorkspace='Vanadium_Raw', Params='0.1,-0.05,5', FullBinsOnly=True, IgnoreBinErrors=True)
ConvertUnits(InputWorkspace='Vanadium_Raw', OutputWorkspace='Vanadium_Raw', Target='Wavelength', AlignBins=True)
Rebin(InputWorkspace='Vanadium_Raw', OutputWorkspace='Vanadium_Raw', Params='0.3,0.7,1,2,3,2,5', FullBinsOnly=True, IgnoreBinErrors=True)

# Mask vanadium: all the masked bins with value equal to zero!
MaskDetectors(Workspace='Vanadium_Raw', MaskedWorkspace='Mask_Background_172362', ForceInstrumentMasking=True)

# Find out the masked detectors
van_raw_ws.getDetector(6468).isMasked()

# ------------------------> Goals
# 1. Find out the original grouping information as masking information
# 2. Mask detectors on the aligned data
# 3. Calculate pixel count weight of "clean" vanadium
# 4. Plot count weight EXCLUDING all the masked pixels