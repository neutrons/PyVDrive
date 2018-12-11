#!/usr/bin/python
# Test the chop and reduce command
import os
import sys
try:
    import qtconsole.inprocess
    from PyQt5.QtWidgets import QApplication
except ImportError:
    from PyQt4.QtGui import QApplication

# create main application
import command_test_setup


def test_ned_simple(tester):
    """ Test the mode simple reduction case for data collected by nED
    :param tester:
    :return:
    """
    # test directory
    test_dir = '/tmp/vbin_ned_simple'
    command_test_setup.set_test_dir(test_dir)

    # run command
    idl_command = "VBIN,IPTS=20280,RUNS=169186,version=2,output=\'{}\'".format(test_dir)
    tester.run_command(idl_command)

    # output summary
    tester.show_output_files(test_dir)

    return


def test_ned_standard(tester):
    """
    :param tester:
    :return:
    """
    # test directory
    test_dir = '/tmp/vbin_ned_tag'
    command_test_setup.set_test_dir(test_dir)

    # run command
    idl_command = "VBIN,IPTS=20280,RUNS=169186,tag='Si',output=\'{}\'".format(test_dir)
    tester.run_command(idl_command)

    # output summary
    tester.show_output_files(test_dir)

    return


def test_ned_user_bin(tester):
    """ Test with min TOF, max TOF and binW
    :param tester:
    :return:
    """
    # test directory
    test_dir = '/tmp/vbin_ned_binw'
    command_test_setup.set_test_dir(test_dir)

    # run command
    idl_command = "VBIN,IPTS=20280,RUNS=169186,version=2, binw=0.002, Mytofbmin=6000.," \
                  "Mytofmax=32500., output=\'{}\'".format(test_dir)
    tester.run_command(idl_command)

    # output summary
    tester.show_output_files(test_dir)

    return


def test_ned_multi_banks(tester):
    """ Test with multiple banks (besides 3)
    :param tester:
    :return:
    """
    # test directory
    test_dir = '/tmp/vbin_ned_binw'
    command_test_setup.set_test_dir(test_dir)

    # run command
    idl_command = "VBIN,IPTS=20280,RUNS=169186,version=2, banks=27, output=\'{}\'".format(test_dir)
    tester.run_command(idl_command)

    # output summary
    tester.show_output_files(test_dir)

    return


def test_ned_mask(tester):
    """
    Test binning with mask
    :param tester:
    :return:
    """
    # test directory
    test_dir = '/tmp/vbin_ned_mask'
    command_test_setup.set_test_dir(test_dir)

    idl_command = 'VBIN,IPTS=20280,RUNS=169186,RUNE=161976,version=2,output=\'{}\',' \
                  'mask=[tests/data/highangle_roi_0607.xml]'.format(test_dir)

    tester.run_command(idl_command)

    # output summary
    tester.show_output_files(test_dir)

    return


def test_main():
    """
    test main
    """
    command_tester = command_test_setup.PyVdriveCommandTestEnvironment()

    test_ned_simple(command_tester)
    test_ned_standard(command_tester)




    #
    # # Test 1 - pre-nED
    # # FIXME - pre-nED case does not work
    # preNed_cmd = "VBIN,IPTS=14094,RUNS=96450, output='/home/wzz/Temp'"
    #
    # # Test 2 - nED case - version 1
    # cmd = 'VBIN,IPTS=20280,RUNS=169186,output=\'/tmp/ver1\''
    # # command_tester.run_command(cmd)
    #
    # # Test 3 - nED case - version 2
    # cmd = 'VBIN,IPTS=20280,RUNS=169186,version=2,output=\'/tmp/ver2\''
    # # command_tester.run_command(cmd)
    #
    # # Test 4 - nED case - version 2 with ROI
    # # VBIN,IPTS=20280,RUNS=169186,RUNE=161976,version=2,output='/tmp/ver2',ROI=[tests/data/highangle_roi_0607.xml]
    # cmd = 'VBIN,IPTS=20280,RUNS=169186,RUNE=161976,version=2,output=\'/tmp/ver2\',' \
    #       'ROI=[tests/data/highangle_roi_0607.xml]'
    # command_tester.run_command(cmd)
    #
    # # Test 5 - nED case - version 2 with ROI
    # cmd = 'VBIN,IPTS=20280,RUNS=169186,RUNE=161976,version=2,output=\'/tmp/ver2\',' \
    #       'ROI=tests/data/highangle_roi_0607.xml' \
    #       ',mask=tests/data/highangle_mask_test.xml'
    # # command_tester.run_command(cmd)
    #
    # ## FIXME/TODO - Check result
    #
    # ## FIXME error message:
    # #cmd = "vbin, ipts=?????, runs=?????, version=2, output='/tmp/ver2'"
    # #cmd = "vbin, ipts=?????, runs=?????, version=1, output='/tmp/ver1/"
    #
    # #print ('Current working dir: {0}'.format(os.getcwd()))
    # #cmd = "vbin, ipts=?????, runs=?????, grouping=l2_group_cal.h5"

    return command_tester.main_window


def main(argv):
    """
    """
    if QApplication.instance():
        _app = QApplication.instance()
    else:
        _app = QApplication(sys.argv)
    return _app

if __name__ == '__main__':
    # Main application
    print ('Test PyVDrive-Commands')
    app = main(sys.argv)

    # this must be here!
    test_window = test_main()
    test_window.show()
    # I cannot close it!  test_window.close()

    app.exec_()

