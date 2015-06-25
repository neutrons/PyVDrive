from lettuce import *
from nose.tools import assert_equals

class MyData:
    def __init__(self):
        self.a = 1.0
        self.b = 2.0
    def __str__(self):
        return "a = %f, b = %f" % (self.a, self.b)

mydata = MyData()
print mydata

@step(u'I am using PyVDrive')
def setUp(step):
    print "Setting up the function test."

    return


@step(u'Given I input IPTS, run number, calibration file name and etc')
def setupParameter(step):
    print "Set up IPTS, run number, and etc. and ", mydata

@step(u'Then I should see a matrix workspace generated')
def reduce(step):
    print "Reducing"
