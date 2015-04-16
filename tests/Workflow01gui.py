################################################################################
#
# This is a script showing a typical workflow to work with VDrive via VDriveAPI
#
################################################################################
import sys
import os
import os.path

import PyVDrive.Ui_VDrive as vdapi

# Initalize a workflow 
myworkflow = vdapi.VDriveAPI()

# initlalize a new project
projname = 'MocknewReductionProj'
if myworkflow.hasProject(projname=projname)[0] is True:
    myworkflow.deleteProject(projname=projname)
myworkflow.newProject(projname=projname, projtype = "reduction")
myworkflow.setDataPath(projname=projname)

# Set IPTS
ipts = 10311

# Set up vanadium run 
# criterialist = [('Frequency', 'float'), ('Guide', 'float'), ('Collimator', 'float')]
vanMatchList = myworkflow._myConfig['vanadium.SampleLogToMatch']
myworkflow.setVanadiumCalibrationMatchCriterion(projname, vanMatchList)

# New project should add data and locate calibration file automatically
runs= range(57075, 57100)
status, errmsg, datafilesets = myworkflow.addExperimentRuns(projname, 'reduction', ipts, runs, True)
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
myworkflow.saveProject('r', projname, projfilename)
myworkflow.deleteProject('r', projname)

myworkflow.loadProject(projfilename)

# add another few runs
runs= range(57079, 57099)
status, errmsg, datafilesets = myworkflow.addExperimentRuns(projname, 'reduction', ipts, runs, False)
if status is False:
    print "Error: \n", errmsg
else:
    msg = "Number of new data files: %d\n" % (len(datafilesets))
    for filepair in datafilesets:
        msg += "Data file: %s, \t\tVanadium run: %s\n" % (filepair[0], filepair[1])
    print "Add new files:\n%s" % (msg)

# save data file again
projfilename = os.path.join(curdir, 'test001a.p')
myworkflow.saveProject('r', projname, projfilename)

# get the information of runs
status, errmsg, datacalpairlist = myworkflow.getDataFiles(projname)
msg = "Data file and calibration file for reduction:\n"
for datapair in sorted(datacalpairlist):
    msg += "%-20s\t\t%-20s\n" % (str(datapair[0]), str(datapair[1]))
print msg

# select the runs to reduce
filestoreduce = [('VULCAN_57075_event.nxs', True), 
    ('VULCAN_57076_event.nxs', True), 
    ('VULCAN_57077_event.nxs', True),
    ('VULCAN_57080_event.nxs', False)]
myworkflow.setReductionFlags('Test001', filestoreduce)
print myworkflow.info(projname)[1]


# delete some run
execstatus, errmsg = myworkflow.deleteRuns(projname, ['arrow.nxs', 'sword.nxs'])
print execstatus, errmsg
execstatus, errmsg = myworkflow.deleteRuns(projname, ['VULCAN_57080_event.nxs'])
print execstatus, errmsg

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
myworkflow.setReductionParameters(projname, paramdict)
myworkflow.reduce(projname)


raise NotImplementedError("Implemented so far...")

# add auxiliary file
#myworkflow.setCalibFile('Test001','dummycalib.dat')
#myworkflow.setCharactFile('Test001','dummychar.txt')



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
