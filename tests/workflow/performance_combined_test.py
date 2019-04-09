#!/usr/bin/python
# Performance test: test a combined set of commands of VBIN, CHOP, VPEAK and MERGE
import os
import sys
import command_test_setup
try:
    from PyQt5.QtWidgets import QApplication
except ImportError:
    from PyQt4.QtGui import QApplication


PASSED = False
TEST_NOW = True


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


def test_vbin_chop_large_set(tester):
    """
    Test CHOP with a long run with large number of events
    :param tester:
    :return:
    """
    print ('[INFO] CHOP on run with large number of events')

    # test directory
    test_dir_1 = '/tmp/combo_large_data_1'
    test_dir_2 = '/tmp/combo_large_data_2'
    command_test_setup.set_test_dir(test_dir_1)
    command_test_setup.set_test_dir(test_dir_2)

    # run command vbin
    idl_command = "vbin,ipts=19589,runs=167677,binfolder=\'{}\'".format(test_dir_1)
    tester.run_command(idl_command)

    # run command chop
    idl_command = "chop,ipts=20280,runs=170461,dbin=300,binfolder=\'{}\'".format(test_dir_2)
    tester.run_command(idl_command)

    # output summary
    tester.show_output_files(test_dir_1)
    tester.show_output_files(test_dir_2)

    return


def test_chop_large_set(tester):
    """
    Test VBIN and CHOP with a long run with large number of events
    :param tester:
    :return:
    """
    print ('[INFO] CHOP on run with large number of events')

    # test directory
    test_dir = '/tmp/chop_large_data'
    command_test_setup.set_test_dir(test_dir)

    # run command
    idl_command = "chop,ipts=20280,runs=170461,dbin=300,binfolder=\'{}\'".format(test_dir)
    tester.run_command(idl_command)

    # output summary
    tester.show_output_files(test_dir)

    return


def acceptance_test_phase1_analysis_cluster(tester):
    """
    Acceptance test for PyVDrive phase 1
    Requirement: This shall be run on analysis cluster
    Here is the sequence of commands to test with
    1. chop, ipts = 22753, runs = 172271, dbin = 120
    2. view, ipts=22753, choprun=172271, runs=2
    3. view, ipts=22753, choprun=172271, runs=1,rune=500, runv=171869
    4. merge, ipts=22753, runlist=172360 & 172362
    5. view,ipts=22753,choprun=172360,runs=1
    6. view,ipts=22753,runs=172360
    7. chop, help=1
    :param tester:
    :return:
    """
    commands_list = ['chop, ipts = 22753, runs = 172271, dbin = 120',
                     'view, ipts=22753, choprun=172271, runs=2',
                     'view, ipts=22753, choprun=172271, runs=1,rune=500, runv=171869',
                     'merge, ipts=22753, runlist=172360 & 172362',
                     'view,ipts=22753,choprun=172360,runs=1',
                     'view,ipts=22753,runs=172360',
                     'chop, help=1']

    # run commands
    for idl_command in commands_list:
        tester.run_command(idl_command)

    # output
    tester.show_output_files('/SNS/VULCAN/IPTS-22753/shared/binned_data/172271')
    tester.show_output_files('/SNS/VULCAN/IPTS-22753/shared/binned_data/172360')

    return


def test_main():
    """
    test main
    """
    command_tester = command_test_setup.PyVdriveCommandTestEnvironment()

    if TEST_NOW:
        acceptance_test_phase1_analysis_cluster(command_tester)

    if PASSED:
        test_vbin_chop_simple(command_tester)

        # large data set for chopping
        test_chop_large_set(command_tester)

        # large data set combo
        test_vbin_chop_large_set(command_tester)
    # END-IF

    return command_tester.main_window


# FIXME TODO - NIGHT - Consider (1) delete original event workspace (2) compress events (3) any other good idea?


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
