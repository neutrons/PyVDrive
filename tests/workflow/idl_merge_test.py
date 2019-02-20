#!/usr/bin/python
# Test the chop and reduce command
import os
import sys
import command_test_setup
try:
    from PyQt5.QtWidgets import QApplication
except ImportError:
    from PyQt4.QtGui import QApplication


Passed = False   # Not test passed


def create_run_file(file_name):
    """
    create a run file on the fly for testing
    :param file_name:
    :return:
    """
    file_str = '171834,171836\n171837,171838\n171840,171839'

    run_file = open(file_name, 'w')
    run_file.write(file_str)
    run_file.close()

    return


def test_ned_vanadium(tester):
    """
    Test PreX/nED data with optiona as vanadium
    :param tester:
    :return:
    """
    # test directory
    test_dir = '/tmp/merge_runv/'
    command_test_setup.set_test_dir(test_dir)

    # run command
    idl_command = "MERGE,IPTS=22752,RUNLIST=171834 & 171836 & 171837 & 171838 & 171840 & 171839," \
                  "RUNV=163021,output=\'{}\'".format(test_dir)
    tester.run_command(idl_command)

    # output summary
    tester.show_output_files(test_dir)

    return


def test_ned_analysis(tester):
    """
    Test PreX/nED data with optiona as vanadium
    :param tester:
    :return:
    """
    # test directory
    test_dir = '/SNS/VULCAN/IPTS-22752/shared/binned_data/171837/'

    # run command
    idl_command = "MERGE,IPTS=22752,RUNLIST=171834 & 171836 & 171837 & 171838 & 171840 & 171839, CHOPRUN=171837"
    tester.run_command(idl_command)

    # output summary
    tester.show_output_files(test_dir)

    return


def test_ned_simple(tester):
    """

    :param tester:
    :return:
    """
    # test directory
    test_dir = '/tmp/merge_simple'
    command_test_setup.set_test_dir(test_dir)

    # create run number file
    run_file_name = os.path.join(test_dir, 'pyvdrive_merge_test.txt')
    create_run_file(run_file_name)

    # run command
    idl_command = "MERGE,IPTS=22752,RUNFILE='{}',CHOPRUN=171836,output=\'{}\'".format(run_file_name, test_dir)
    tester.run_command(idl_command)

    # output summary
    tester.show_output_files(test_dir)

    return


def test_main():
    """
    test main
    """
    command_tester = command_test_setup.PyVdriveCommandTestEnvironment()

    if Passed:
        test_ned_simple(command_tester)
        test_ned_vanadium(command_tester)
    else:
        test_ned_analysis(command_tester)

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
 
