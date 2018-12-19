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


def test_multiple_masks(tester):
    """
    Testing multiple masks
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


def test_multiple_roi(tester):
    """
    Testing multiple region of interest
    :param tester:
    :return:
    """
    # test directory
    test_dir = '/tmp/vbin_ned_roi'
    command_test_setup.set_test_dir(test_dir)

    idl_command = 'VBIN,IPTS=20280,RUNS=169186,RUNE=161976,version=2,output=\'{}\',' \
                  'mask=[tests/data/highangle_roi_0607.xml, tests/data/highangle_roi_0608.xml]'.format(test_dir)

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
    # test_ned_standard(command_tester)
    # test_ned_user_bin(command_tester)
    # test_ned_multi_banks(command_tester)
    # test_ned_mask()
    # test_ned_roi()

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

