################################################################################
#
#This is a script showing a typical workflow to work with VDrive
#
################################################################################

import sys
# sys.path.append('/home/wzz/local/lib/python2.7/Site-Packages/')

import PyVDrive.Ui_VDrive as vdapi

myworkflow = vdapi.VDriveAPI()

# initlalize a new project
if myworkflow.hasProject(projname='Test001')[0] is True:
    myworkflow.deleteProject(projname='Test0001')
myworkflow.newProject(projname = "Test001", projtype = "reduction")

# new project should add data and locate calibration file automatically
ipts = 10311
runs= range(57080, 57100)

criterialist = [('Frequency', 'float'), ('Guide', 'float'), ('Collimator', 'float')]
myworkflow.setVanadiumCalibrationMatchCriterion('Test001', criterialist)
status, errmsg = myworkflow.addExperimentRuns('Test001', 'reduction', ipts, runs, True)
if status is False:
    print "Error: \n", errmsg

myworkflow.saveProject('r', 'Test001', '/home/wzz/Projects/PyVDrive/PyVDrive/tests/test001.p')
myworkflow.deleteProject('r', 'Test001')

myworkflow.loadProject('/home/wzz/Projects/PyVDrive/PyVDrive/tests/test001.p')


raise NotImplementedError("Implemented so far...")

# add auxiliary file
#myworkflow.setCalibFile('Test001','dummycalib.dat')
#myworkflow.setCharactFile('Test001','dummychar.txt')


outputdir = "/tmp/"

# set reduction parameters
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

myworkflow.setReductionParameters('Test001', paramdict)

# reduce
myworkflow.reduce('Test001')
