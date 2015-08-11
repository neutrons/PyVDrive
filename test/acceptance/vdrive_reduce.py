from lettuce import *
from nose.tools import assert_equals

import sys
import os
import os.path

sys.path.append('/home/wzz/local/lib/python2.7/Site-Packages/')
import PyVDrive.Ui_VDrive as vdapi

class MyData:
    def __init__(self):
        """ Init
        """
        self.myObject = None

    def __str__(self):
        """ Nice output
        """
        return str(self.myObject)


    def get(self):
        """ Get
        """
        return self.myObject

    def set(self, inputobject):
        """ Set
        """
        if inputobject is None:
            raise NotImplementedError("Input object is not supposed to be None.")

        self.myObject = inputobject

        return

mydata = MyData()

@step(u'I am using PyVDrive')
def setUp(step):
    """ Set up 
    """
    wkflow =  vdapi.VDriveAPI()
    mydata.set(wkflow)

    return

@step(u'Given I input IPTS, run number, calibration file name and etc')
def setupReduction(step):
    """ Set up IPTS, run number and etc for reduction
    """
    wkflow = mydata.get()
    # new project
    wkflow.newProject(projname = "Test001", projtype = "reduction")
    # set data path with default
    wkflow.setDataPath(projname = 'Test001')
    # IPTS and runs
    ipts = 10311
    runs= range(57070, 57078)

    # FIXME : Should be put to 2 different test cases in future
    if False:
        # Manual setup
        wkflow.setVanadiumFile('/SNS/VULCAN/shared/Calibrationfiles/Instrument/Standard/Vanadium/VRecord.txt')
        criterialist = [('Frequency', 'float'), ('Guide', 'float'), ('Collimator', 'float')]
        # set vanadium calibration (new project should add data and locate calibration file automatically)
        wkflow.setVanadiumCalibrationMatchCriterion('Test001', criterialist)
        # add experiment 
        status, errmsg, datafilesets = wkflow.addExperimentRuns('Test001', 'reduction', ipts, runs, True)

    else:
        # Automatic setup
        r = wkflow.addExperimentRuns(projname='Test001', operation='Add Experiment Runs', ipts=ipts, 
                runnumberlist=runs, autofindcal=True)
    # ENDIFELSE


    return

@step(u'Then I reduce the data')
def reduceData(step):
    """ Set up reduction parametera and reduce data
    """
    wkflow = mydata.get()

    wkflow.setInstrumentName('VULCAN')
    wkflow.setCalibrationFile(projname ='Test001', 
            calibfilename = '/SNS/VULCAN/shared/autoreduce/vulcan_foc_all_2bank_11p.cal')

    # set up reduction parameters
    outputdir = os.getcwd()
    paramdict = {
            "Extension": "_event.nxs",
            "PreserveEvents": True,
            "Binning" : -0.001,
            "OutputDirectory" : outputdir, 
            "NormalizeByCurrent":  False,
            "FilterBadPulses": False,
            "CompressTOFTolerance": False,
            "FrequencyLogNames": "skf1.speed",
            "WaveLengthLogNames": "skf12.lambda"
            }
    wkflow.setReductionParameters('Test001', paramdict)

    # reduce
    reductionlist = [ ('VULCAN_57075_event.nxs', True) ]

    wkflow.setReductionFlags(projname='Test001', filepairlist=reductionlist)
    wkflow.reduceData(projname='Test001', normByVan=False, tofmin=None, tofmax=None)

    return

@step(u'Then I should see a matrix workspace generated')
def retrieveReducedData(step):
    wkflow = mydata.get()

    reducedrunlist = wkflow.getReducedRuns(projectname = 'Test001')
    numredws = len(reducedrunlist)
    assert_equals(numredws, 1)

    print "Retrieve reduced data"
