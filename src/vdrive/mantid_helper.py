import sys
import os
import os.path

"""
# FIXME : This is for local development only!
homedir = os.path.expanduser('~')
mantidpath = os.path.join(homedir, 'Mantid/Code/debug/bin/')
sys.path.append(mantidpath)
"""

# import mantid
import mantid.simpleapi as mantidapi

def loadNexus(datafilename, outwsname, metadataonly):
    """
    :param datafilename:
    :param outwsname:
    :param metadataonly:
    :return:
    """
    try:
        outws = mantidapi.Load(Filename=datafilename,
                               OutputWorkspace=outwsname,
                               MetaDataOlny=metadataonly)
    except RuntimeError as e:
        return False, str(e), None

    return True, '', outws