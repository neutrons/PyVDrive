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
    """

    :param tester:
    :return:
    """
    # test directory
    test_dir = '/tmp/merge/simple'
    command_test_setup.set_test_dir(test_dir)

    run_file_name =

    # run command
    idl_command = "MERGE,IPTS=21356,RUNFILE='{}',output=\'{}\'".format(run_file_name, test_dir)
    tester.run_command(idl_command)

    # output summary
    print ('Command {} has been executed.'.format(idl_command))

    return


def test_main():
    """
    test main
    """
    command_tester = command_test_setup.PyVdriveCommandTestEnvironment()

    test_ned_simple(command_tester)