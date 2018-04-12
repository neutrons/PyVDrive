import h5py
import math


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
    CreateWorkspace(DataX=west_spec_vec, DataY=west_difc_vec, NSpec=1, OutputWorkspace='west_difc')

    # east bank
    CreateWorkspace(DataX=east_spec_vec, DataY=east_difc_vec, NSpec=1, OutputWorkspace='eastt_difc')

    # high angle bank
    CreateWorkspace(DataX=highangle_spec_vec, DataY=highangle_difc_vec, NSpec=1, OutputWorkspace='hig_angle_difc')


