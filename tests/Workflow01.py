################################################################################
#
#This is a script showing a typical workflow to work with VDrive
#
################################################################################

import sys
import os
import os.path
# sys.path.append('/home/wzz/local/lib/python2.7/Site-Packages/')

import PyVDrive.Ui_VDrive as vdapi

myworkflow = vdapi.VDriveAPI()

# initlalize a new project
if myworkflow.hasProject(projname='Test001')[0] is True:
    myworkflow.deleteProject(projname='Test0001')
myworkflow.newProject(projname = "Test001", projtype = "reduction")
myworkflow.setDataPath(projname = 'Test001', basedatapath = '/Users/wzz/Projects/SNSData/VULCAN')

# new project should add data and locate calibration file automatically
ipts = 10311
runs= range(57070, 57078)

criterialist = [('Frequency', 'float'), ('Guide', 'float'), ('Collimator', 'float')]
myworkflow.setVanadiumCalibrationMatchCriterion('Test001', criterialist)
status, errmsg, datafilesets = myworkflow.addExperimentRuns('Test001', 'reduction', ipts, runs, True)
if status is False:
    print "Error: \n", errmsg
else:
    msg = "Number of new data files: %d\n" % (len(datafilesets))
    for filepair in datafilesets:
        msg += "Data file: %s, \t\tVanadium run: %s\n" % (filepair[0], filepair[1])
    print "Add new files:\n%s" % (msg)

# save and load project
curdir = os.getcwd()
projfilename = os.path.join(curdir, 'test001.p')
myworkflow.saveProject('r', 'Test001', projfilename)
myworkflow.deleteProject('r', 'Test001')

myworkflow.loadProject(projfilename)

# add another few runs
runs= range(57079, 57099)
status, errmsg, datafilesets = myworkflow.addExperimentRuns('Test001', 'reduction', ipts, runs, False)
if status is False:
    print "Error: \n", errmsg
else:
    msg = "Number of new data files: %d\n" % (len(datafilesets))
    for filepair in datafilesets:
        msg += "Data file: %s, \t\tVanadium run: %s\n" % (filepair[0], filepair[1])
    print "Add new files:\n%s" % (msg)

# save data file again
projfilename = os.path.join(curdir, 'test001a.p')
myworkflow.saveProject('r', 'Test001', projfilename)

# get the information of runs
datacalpairlist = myworkflow.getDataFiles('Test001')
msg = "Data file and calibration file for reduction:\n"
for datapair in sorted(datacalpairlist):
    msg += "%-20s\t\t%-20s\n" % (datapair[0], datapair[1])
print msg


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
