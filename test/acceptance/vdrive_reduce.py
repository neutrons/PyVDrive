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
    criterialist = [('Frequency', 'float'), ('Guide', 'float'), ('Collimator', 'float')]
    # set vanadium calibration (new project should add data and locate calibration file automatically)
    wkflow.setVanadiumCalibrationMatchCriterion('Test001', criterialist)
    # add experiment 
    status, errmsg, datafilesets = wkflow.addExperimentRuns('Test001', 'reduction', ipts, runs, True)

    return

@step(u'Then I reduce the data')
def reduceData(step):
    """ Set up reduction parametera and reduce data
    """
    wkflow = mydata.get()

    # set up reduction parameters
    outputdir = os.getcwd()
    paramdict = {
            "Instrument": "VULCAN",
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
    wkflow.reduceData('Test001')

    return

@step(u'Then I should see a matrix workspace generated')
def retrieveReducedData(step):
    print "Retrieve reduced data"
