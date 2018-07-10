# This is the second round of cross-correlation


    # peak position in d-Spacing
    peakpos1 = 1.2614
    peakpos2 = 1.2614
    peakpos3 = 1.07577

def second_cc():
    Load(Filename='/SNS/VULCAN/IPTS-21356/nexus/VULCAN_161364.nxs.h5', OutputWorkspace='vulcan_diamond')
    LoadDiffCal(InputWorkspace='vulcan_diamond', Filename='/SNS/users/wzz/Projects/VULCAN/Calibration_20180530/vulcan_2fit.h5', WorkspaceName='vulcan')
    LoadDiffCal(InputWorkspace='vulcan_diamond', Filename='/SNS/users/wzz/Projects/VULCAN/Calibration_20180530/VULCAN_calibrate_2018_04_12.h5', WorkspaceName='vulcanold')
    AlignDetectors(InputWorkspace='vulcan_diamond', OutputWorkspace='vulcan_diamond', CalibrationWorkspace='vulcan_cal')
    DiffractionFocussing(InputWorkspace='vulcan_diamond', OutputWorkspace='vulcan_diamond', GroupingWorkspace='vulcanold_group')
    Rebin(InputWorkspace='vulcan_diamond', OutputWorkspace='vulcan_diamond', Params='0.5,-0.0003,3')
    ConvertToMatrixWorkspace(InputWorkspace='vulcan_diamond', OutputWorkspace='vulcan_diamond_3bank')
    EditInstrumentGeometry(Workspace='vulcan_diamond_3bank', PrimaryFlightPath=42, SpectrumIDs='1-3', L2='2,2,2', Polar='89.9284,90.0716,150.059', Azimuthal='0,0,0', DetectorIDs='1-3', InstrumentName='vulcan_3bank')
    CrossCorrelate(InputWorkspace='vulcan_diamond_3bank', OutputWorkspace='cc_vulcan_diamond_3bank', ReferenceSpectra=1, WorkspaceIndexMax=2, XMin=1.0649999999999999, XMax=1.083)
    GetDetectorOffsets(InputWorkspace='cc_vulcan_diamond_3bank', Step=0.00029999999999999997, DReference=1.0757699999999999, XMin=-20, XMax=20, OutputWorkspace='zz_test_3bank', FitEachPeakTwice=True, PeakFitResultTableWorkspace='ddd', OutputFitResult=True, MinimumPeakHeight=1)



def apply_second_cc():
offset_ws = mtd['vulcan_foc_cal_offsets']
shift_offset_ws  = CloneWorkspace(InputWorkspace=offset_ws, OutputWorkspace='offset_test')
for iws in range(0, 3234):
    shift_offset_ws.dataY(iws)[0] *= 1+1.0938E-4
for iws in range(6468, 24900):
    shift_offset_ws.dataY(iws)[0] *= 1 - 1.3423E-4
    
        
    


