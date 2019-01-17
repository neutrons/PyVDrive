#!/usr/bin/python
# Performance test: test a combined set of commands of VBIN, CHOP, VPEAK and MERGE
import os
import sys
import command_test_setup
try:
    from PyQt5.QtWidgets import QApplication
except ImportError:
    from PyQt4.QtGui import QApplication


def test_vbin_chop_simple(tester):
    """
    Test a set of commands including VBIN, CHOP
    Data will be relatively smaller in order to test potential conflict
    :return:
    """
    #
    # run: VBIN,IPTS=20280,RUNS=169186, output='/tmp/'
    # run: chop, ipts=20717, runs=170464, dbin=30, loadframe=1, output='/tmp'

    print ('[INFO] Combined commands performance test')

    # test directory
    test_dir = '/tmp/vbin_combined'
    command_test_setup.set_test_dir(test_dir)

    # run command
    idl_command = "VBIN,IPTS=20280,RUNS=169186,version=2,output=\'{}\'".format(test_dir)
    tester.run_command(idl_command)

    idl_command = 'chop, ipts=20717, runs=170464, dbin=30, loadframe=1, output=\'{}\''.format(test_dir)
    tester.run_command(idl_command)

    # output summary
    tester.show_output_files(test_dir)

    return


def test_vbin_large_set(tester):
    """
    Test VBIN with a long run with large number of events
    :return:
    """
    print ('[INFO] VBIN on run with large number of events')

    # test directory
    test_dir = '/tmp/vbin_large_data'
    command_test_setup.set_test_dir(test_dir)

    # run command
    idl_command = "vbin,ipts=20280,runs=170461,binfolder=\'{}\'".format(test_dir)
    tester.run_command(idl_command)

    # output summary
    tester.show_output_files(test_dir)

    return


def test_chop_large_set(tester):
    """
    Test CHOP with a long run with large number of events
    :param tester:
    :return:
    """
    print ('[INFO] CHOP on run with large number of events')

    # test directory
    test_dir_1 = '/tmp/chop_large_data_1'
    test_dir_2 = '/tmp/chop_large_data_2'
    command_test_setup.set_test_dir(test_dir)

    # run command vbin
    # TODO - DAYTIME - Find a different large run in another IPTS
    idl_command = "vbin,ipts=20280,runs=170461,binfolder=\'{}\'".format(test_dir_1)
    tester.run_command(idl_command)

    # run command chop
    idl_command = "chop,ipts=20280,runs=170461,dbin=300,binfolder=\'{}\'".format(test_dir_2)
    tester.run_command(idl_command)

    # output summary
    tester.show_output_files(test_dir_1)
    tester.show_output_files(test_dir_2)

    return


def test_vbin_chop_larget_set(tester):
    """
    Test VBIN and CHOP with a long run with large number of events
    :param tester:
    :return:
    """
    print ('[INFO] CHOP on run with large number of events')

    # test directory
    test_dir = '/tmp/combo_large_data'
    command_test_setup.set_test_dir(test_dir)

    # run command
    idl_command = "chop,ipts=20280,runs=170461,dbin=300,binfolder=\'{}\'".format(test_dir)
    tester.run_command(idl_command)

    # output summary
    tester.show_output_files(test_dir)



def test_main():
    """
    test main
    """
    command_tester = command_test_setup.PyVdriveCommandTestEnvironment()

    test_vbin_chop_simple(command_tester)

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
