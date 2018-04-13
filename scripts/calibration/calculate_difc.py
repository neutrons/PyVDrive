import h5py
import numpy
import math
from mantid.api import AnalysisDataService as mtd
from mantid.simpleapi import CreateWorkspace


def get_idf_difc():
    ws = mtd['ws_10h']
    
    out = ''
    
    # This is the theoretical DIFC
    for i in range(ws.getNumberHistograms()):
        det_id = ws.getDetector(i).getID()
        det_pos = ws.getDetector(i).getPos()
        source_pos = ws.getInstrument().getSource().getPos()
        sample_pos = ws.getInstrument().getSample().getPos()
        
        source_sample =  sample_pos - source_pos
        det_sample = det_pos - sample_pos
        angle = det_sample.angle(source_sample)
        
        L1 = source_sample.norm()
        L2 = det_sample.norm()
       
        
        # theta = angle * 180/3.14
        # print theta
        
        difc = 252.816 * 2 * math.sin(angle*0.5) * (L1+L2)  # math.sqrt(L1+L2) #\sqrt{L1+L2}
        
        out += '{0}  {1}  {2}\n'.format(i, det_id, difc)
        
    # end-for
    
    out_file = open('raw_difc.dat', 'w')
    out_file.write(out)
    out_file.close()


def get_calibrated_difc(cal_ws_name):
    """ go over calibration (table) workspace
    """
    cal_table_ws = mtd[cal_ws_name]

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
        west_difc_vec[irow-3234] = cal_table_ws.cell(irow, difc_col_index)

    CreateWorkspace(DataX=east_spec_vec, DataY=east_difc_vec, NSpec=1, OutputWorkspace='eastt_difc')

    # high angle bank
    highangle_spec_vec = numpy.arange(6468, 49000)
    highangle_difc_vec = numpy.ndarray(shape=(3234,), dtype='float')
    for irow in range(6468, 49000):
        west_difc_vec[irow-6468] = cal_table_ws.cell(irow, difc_col_index)

    CreateWorkspace(DataX=highangle_spec_vec, DataY=highangle_difc_vec, NSpec=1, OutputWorkspace='hig_angle_difc')

    return


if 'diamond' not in mtd:
    Load(Filename='/SNS/VULCAN/IPTS-19576/nexus/VULCAN_160457.nxs.h5', OutputWorkspace='diamond')
LoadDiffCal(InputWorkspace='diamond',
            Filename='/home/wzz/Vulcan-Calibration/2017_8_11_CAL/VULCAN_calibrate_2017_08_17_27bank.h5',
            WorkspaceName='vulcan_27')