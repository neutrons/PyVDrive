import unittest
import sys
sys.path.append('/home/wzz/local/lib/python2.7/Site-Packages')

import PyVDrive
import PyVDrive.vdrive
import PyVDrive.vdrive.VDProject as vp

class TddReductionProject(unittest.TestCase):
    def setUp(self):
        self.project = vp.ReductionProject('Test')

    def test_basepath_setup(self):
        basepath = '/SNS/VULCAN/'
        self.project.setBaseDataPath(basepath)
        basepath2 = self.project.getBaseDataPath()
        self.assertbasepath, basepath2)

        return

    def test_addData(self):
        datafilename = '/SNS/VULCAN/IPTS-1234/0/VULCAN_12345_events.nxs'
        self.project.addData(datafilename)
        self.assertEqual(len(project._dataset), 1)
        self.assertEqual(project._baseDataFileNameList[0], 'VULCAN_12345_events.nxs')



if __name__ == "__main__":
    unittest.main()
