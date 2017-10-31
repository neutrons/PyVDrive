################################################################################
# Configuration file: config.py
# Should be stored in ~/.vdrive/ in deployment
################################################################################
import os

# global definitions for constants and variables


# Table column heading indicies for reduction
fileName = 0
vanRun = 1
reduceIt = 2

# Data path
datapaths = ['/SNS/VULCAN/', '~/Projects/SNSData/VULCAN']
defaultDataPath = None
for datapath in datapaths:
    # replace ~ by absolute path
    if datapath.startswith('~') is True:
        datapath = datapath.replace('~', os.path.expanduser('~'))

    if os.path.exists(datapath) is True:
        defaultDataPath = datapath
        break
# ENDFOR

# Vanadium
vanadiumDataBaseFiles = [ 
    '/SNS/VULCAN/shared/Calibrationfiles/Instrument/Standard/Vanadium/VRecord.txt', 
    '~/Projects/SNSData/VULCAN/shared/Calibrationfiles/Instrument/Standard/Vanadium/VRecord.txt']
defaultVanadiumDataBaseFile = None
for vanfilename in vanadiumDataBaseFiles:
    # replace ~ by absolute path
    if vanfilename.startswith('~') is True:
        vanfilename = vanfilename.replace('~', os.path.expanduser('~'))

    if os.path.exists(vanfilename) is True:
        defaultVanadiumDataBaseFile = vanfilename
        break
# ENDFOR

#------------------------------------------------------------------------------
# Finally
#------------------------------------------------------------------------------
# Build the configuration dictionry
configdict = {}
configdict['default.BaseDataPath'] = defaultDataPath
configdict['default.VanadiumDataBaseFile'] = defaultVanadiumDataBaseFile
configdict['default.timeFocusFile'] = '/SNS/VULCAN/shared/autoreduce/vulcan_foc_all_2bank_11p.cal'

configdict['vanadium.SampleLogToMatch'] = [('Guide', 'float'), ('BandWidth', 'float'), ('Frequency', 'float')]
