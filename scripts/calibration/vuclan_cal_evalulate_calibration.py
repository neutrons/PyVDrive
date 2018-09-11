# It is to evaluate the calibration result


def load_raw_nexus(ipts_number, run_number, calib_file_name):
    """
    reduced: aligned detector and diffraction focus, powder data
    :param ipts_number:
    :param run_number:
    :return:
    """
    raw_nxs_file_name = '/SNS/VULCAN/IPTS-{}/nexus/VULCAN_{}.nxs.h5'.format(ipts_number, run_number)
    Load(Filename=raw_nxs_file_name, OutputWorkspace='vulcan_diamond')

    return

def load_calibration_file():

    # load data file
    LoadDiffCal(InputWorkspace='vulcan_diamond',
                Filename=calib_file_name, WorkspaceName='vulcan')



def analysize_mask():
    """
    """
    # TODO - 20180910 - Implement!

    # 1. Load original event workspace

    # 2. For each bank, sort the masked workspace from highest ban


def align_detectors():

    AlignDetectors(InputWorkspace='vulcan_diamond', OutputWorkspace='vulcan_diamond',
                   CalibrationWorkspace='vulcan_cal')

def diffraction_focus():

    DiffractionFocussing(InputWorkspace='vulcan_diamond', OutputWorkspace='vulcan_diamond',
                         GroupingWorkspace='vulcan_group')

    Rebin(InputWorkspace='vulcan_diamond', OutputWorkspace='vulcan_diamond', Params='0.5,-0.0003,3')

    ConvertToMatrixWorkspace(InputWorkspace='vulcan_diamond', OutputWorkspace='vulcan_diamond_3bank')

    EditInstrumentGeometry(Workspace='vulcan_diamond_3bank', PrimaryFlightPath=42, SpectrumIDs='1-3', L2='2,2,2',
                           Polar='89.9284,90.0716,150.059', Azimuthal='0,0,0', DetectorIDs='1-3',
                           InstrumentName='vulcan_3bank')

