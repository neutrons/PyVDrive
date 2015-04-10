################################################################################
# Test for workflow - 02: Start an analysis project
################################################################################

import sys
import os
import os.path

import PyVDrive.Ui_VDrive as vdapi
import PyVDrive.config as vconfig

print "Default data path = ", vconfig.defaultDataPath

myworkflow = vdapi.VDriveAPI()

# initlalize a new project
myProjectName = 'Test002'

if myworkflow.hasProject(projname=myProjectName)[0] is True:
    myworkflow.deleteProject(projname=myProjectName)
myworkflow.newProject(projname = myProjectName, projtype = "analysis")

# with data path is set up, need to manually add all GSAS data under the specified directory
myworkflow.addData(projname=myProjectname, datadir='/Users/wzz/.../IPTS-???')


