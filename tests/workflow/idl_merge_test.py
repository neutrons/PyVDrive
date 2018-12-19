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


def create_run_file(file_name):
    """
    create a run file on the fly for testing
    :param file_name:
    :return:
    """
    file_str = '12345, 12356\n13456\t12343\n12345'

    run_file = open(file_name, 'w')
    run_file.write(file_str)
    run_file.close()

    return


def test_ned_simple(tester):
    """

    :param tester:
    :return:
    """
    # test directory
    test_dir = '/tmp/merge/simple'
    command_test_setup.set_test_dir(test_dir)

    run_file_name = os.path.join(test_dir, 'pyvdrive_merge_test.txt')

    # run command
    idl_command = "MERGE,IPTS=21356,RUNFILE='{}',output=\'{}\'".format(run_file_name, test_dir)
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