################################################################################
#
# Modified SNS Powder Reduction
#
################################################################################

sys.path.append("/home/wzz/Mantid/Code/debug/bin/")
sys.path.append("/Users/wzz/Mantid/Code/debug/bin/")

import mantid
import mantid.simpleapi as mtd

class SNSPowderReductionLite:
    """ Class SNSPowderReductionLite 
    is a light version of SNSPowderReduction. 
    
    It is able to reduce the data file in the format of data file, 
    run number and etc. 

    It supports event chopping. 
    """
    def __init__(self, calibfname):
        """ Init
        """
        self._calibfilename = calibfname

        return
