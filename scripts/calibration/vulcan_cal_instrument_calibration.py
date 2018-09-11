# This is the second round of cross-correlation in order to
# cross-correlate/align 3 already-focused banks (west, east and high angle) to the same peak positions

from mantid.simpleapi import Load, LoadDiffCal, AlignDetectors, DiffractionFocussing, Rebin, EditInstrumentGeometry
from mantid.simpleapi import ConvertToMatrixWorkspace, CrossCorrelate, GetDetectorOffsets


# (hard coded) diamond peak position in d-Spacing
Diamond_Peaks_1 = 1.2614
peakpos2 = 1.2614
peakpos3 = 1.07577


def reduced_powder_data(ipts_number, run_number, calib_file_name):
    """
    reduced: aligned detector and diffraction focus, powder data
    :param ipts_number:
    :param run_number:
    :return:
    """
    raw_nxs_file_name = '/SNS/VULCAN/IPTS-{}/nexus/VULCAN_{}.nxs.h5'.format(ipts_number, run_number)
    Load(Filename=raw_nxs_file_name, OutputWorkspace='vulcan_diamond')

    # load data file
    LoadDiffCal(InputWorkspace='vulcan_diamond',
                Filename=calib_file_name, WorkspaceName='vulcan')

    AlignDetectors(InputWorkspace='vulcan_diamond', OutputWorkspace='vulcan_diamond',
                   CalibrationWorkspace='vulcan_cal')

    DiffractionFocussing(InputWorkspace='vulcan_diamond', OutputWorkspace='vulcan_diamond',
                         GroupingWorkspace='vulcan_group')

    Rebin(InputWorkspace='vulcan_diamond', OutputWorkspace='vulcan_diamond', Params='0.5,-0.0003,3')

    ConvertToMatrixWorkspace(InputWorkspace='vulcan_diamond', OutputWorkspace='vulcan_diamond_3bank')

    EditInstrumentGeometry(Workspace='vulcan_diamond_3bank', PrimaryFlightPath=42, SpectrumIDs='1-3', L2='2,2,2',
                           Polar='89.9284,90.0716,150.059', Azimuthal='0,0,0', DetectorIDs='1-3',
                           InstrumentName='vulcan_3bank')

    return


def cross_instrument_calibration():
    """
    Main algorithm to do cross-correlation among different banks of VULCAN.
    This is the second round calibration using the data file
    1. calibrated by previous calibration file based on inner bank cross correlation
    2. diffraction focused
    For the instrument with west, east and high angle banks, the input file shall be a 3 bank
    :return:
    """


    CrossCorrelate(InputWorkspace='vulcan_diamond_3bank', OutputWorkspace='cc_vulcan_diamond_3bank', ReferenceSpectra=1, WorkspaceIndexMax=2, XMin=1.0649999999999999, XMax=1.083)
    GetDetectorOffsets(InputWorkspace='cc_vulcan_diamond_3bank', Step=0.00029999999999999997, DReference=1.0757699999999999, XMin=-20, XMax=20, OutputWorkspace='zz_test_3bank', FitEachPeakTwice=True, PeakFitResultTableWorkspace='ddd', OutputFitResult=True, MinimumPeakHeight=1)



def apply_second_cc():
    """
    apply the result of second round cross correlation
    """
    offset_ws = mtd['vulcan_foc_cal_offsets']
    shift_offset_ws  = CloneWorkspace(InputWorkspace=offset_ws, OutputWorkspace='offset_test')
    for iws in range(0, 3234):
        shift_offset_ws.dataY(iws)[0] *= 1+1.0938E-4
    for iws in range(6468, 24900):
        shift_offset_ws.dataY(iws)[0] *= 1 - 1.3423E-4apply_second_cc



if __name__ == '__main__':

    calib_file_name = '/SNS/users/wzz/Projects/VULCAN/Calibration_20180530/vulcan_2fit.h5'
    
        
    


