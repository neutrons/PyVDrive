from lettuce import *
from nose.tools import assert_equals, assert_true, assert_false

import sys

@step(u'I am using mantid helper')
def init_background(step):
    """
    Import packages

    Note: No print will be directed to terminal.  But the method is executed.
    """
    sys.path.append('/home/wzz/local/lib/python2.7/Site-Packages/')
    import PyVDrive.VDriveAPI as vdapi

    return 

@step(u'I know the IPTS number and run number of a run for silicon')
def init_test(step):
    """ Intialize the test including
    """
    import PyVDrive.vdrive.mantid_helper
    print 'Test case: IPTS 13587  Run 70269 for silicon. FCC a=b=c=5.43, F d 3 m'
    print 'Test case: IPTS 13587  Run 66623 for unknown FCC material'

    print

    return


@step(u'I input the lattice parameters of silicon and calculate the reflections in d spacing.')
def setup_ipts(step):
    """ Set up IPTS, run number and etc for reduction
    """
    # TODO/NOW/1st - Implement this!

    return



