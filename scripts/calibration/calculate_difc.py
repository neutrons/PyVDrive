import h5py
import numpy
import math
from mantid.api import AnalysisDataService as mtd
from mantid.simpleapi import CreateWorkspace


def get_idf_difc(ws):
    """
    calculate IDF from DIFC
    :param ws:
    :return:
    """
    def calcualte_difc(ws, ws_index):
        # det_id = ws.getDetector(i).getID()
        det_pos = ws.getDetector(ws_index).getPos()
        source_pos = ws.getInstrument().getSource().getPos()
        sample_pos = ws.getInstrument().getSample().getPos()

        source_sample = sample_pos - source_pos
        det_sample = det_pos - sample_pos
        angle = det_sample.angle(source_sample)

        L1 = source_sample.norm()
        L2 = det_sample.norm()

        # theta = angle * 180/3.14
        # print theta

        difc = 252.816 * 2 * math.sin(angle * 0.5) * (L1 + L2)  # math.sqrt(L1+L2) #\sqrt{L1+L2}

        return difc

    # west bank
    west_spec_vec = numpy.arange(0, 3234)
    west_difc_vec = numpy.ndarray(shape=(3234,), dtype='float')
    for irow in range(0, 3234):
        west_difc_vec[irow] = calcualte_difc(ws, irow)

    CreateWorkspace(DataX=west_spec_vec, DataY=west_difc_vec, NSpec=1, OutputWorkspace='west_idf_difc')

    # east bank
    east_spec_vec = numpy.arange(3234, 6468)
    east_difc_vec = numpy.ndarray(shape=(3234,), dtype='float')
    for irow in range(3234, 6468):
        east_difc_vec[irow-3234] = calcualte_difc(ws, irow)

    CreateWorkspace(DataX=east_spec_vec, DataY=east_difc_vec, NSpec=1, OutputWorkspace='east_idf_difc')

    # high angle bank
    highangle_spec_vec = numpy.arange(6468, 24900)
    highangle_difc_vec = numpy.ndarray(shape=(24900-6468,), dtype='float')
    for irow in range(6468, 24900):
        highangle_difc_vec[irow-6468] = calcualte_difc(ws, irow)

    CreateWorkspace(DataX=highangle_spec_vec, DataY=highangle_difc_vec, NSpec=1, OutputWorkspace='high_angle_idf_difc')

    # This is the theoretical DIFC FIXME Output is disabled
    # for i in range(ws.getNumberHistograms()):
    #
    #
    #     out += '{0}  {1}  {2}\n'.format(i, det_id, difc)
    #
    # # end-for
    #
    # out_file = open('raw_difc.dat', 'w')
    # out_file.write(out)
    # out_file.close()

    return


def get_calibrated_difc(cal_ws_name):
    """ go over calibration (table) workspace
    """
    cal_table_ws = mtd[cal_ws_name]
    difc_col_index = 1

    # west bank
    west_spec_vec = numpy.arange(0, 3234)
    west_difc_vec = numpy.ndarray(shape=(3234,), dtype='float')
    for irow in range(0, 3234):
        west_difc_vec[irow] = cal_table_ws.cell(irow, difc_col_index)

    CreateWorkspace(DataX=west_spec_vec, DataY=west_difc_vec, NSpec=1, OutputWorkspace='west_difc')

    # east bank
    east_spec_vec = numpy.arange(3234, 6468)
    east_difc_vec = numpy.ndarray(shape=(3234,), dtype='float')
    for irow in range(3234, 6468):
        east_difc_vec[irow-3234] = cal_table_ws.cell(irow, difc_col_index)

    CreateWorkspace(DataX=east_spec_vec, DataY=east_difc_vec, NSpec=1, OutputWorkspace='east_difc')

    # high angle bank
    highangle_spec_vec = numpy.arange(6468, 24900)
    highangle_difc_vec = numpy.ndarray(shape=(24900-6468,), dtype='float')
    for irow in range(6468, 24900):
        highangle_difc_vec[irow-6468] = cal_table_ws.cell(irow, difc_col_index)

    CreateWorkspace(DataX=highangle_spec_vec, DataY=highangle_difc_vec, NSpec=1, OutputWorkspace='hig_angle_difc')

    return


def main():
    if 'diamond' not in mtd:
        diamond_ws = Load(Filename='/SNS/VULCAN/IPTS-19576/nexus/VULCAN_160457.nxs.h5', OutputWorkspace='diamond')
    else:
        diamond_ws = mtd['diamond']

    # get IDF DIFC
    # get_idf_difc(diamond_ws)

    # calculate calibrated DIFC
    if 'vulcan_27_cal' not in mtd:
        LoadDiffCal(InputWorkspace='diamond',
                    Filename='/home/wzz/Vulcan-Calibration/2017_8_11_CAL/VULCAN_calibrate_2017_08_17_27bank.h5',
                    WorkspaceName='vulcan_27')

    get_calibrated_difc('vulcan_27_cal')
    get_idf_difc(diamond_ws)

main()

