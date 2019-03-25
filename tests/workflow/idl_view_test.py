#!/usr/bin/python
# Test the IDL-like command VIEW/VDRIVEVIEW
import sys
import command_test_setup
try:
    from PyQt5.QtWidgets import QApplication
except ImportError as import_error:
    print ('[idl_view_test] Import PyQt5/qtconsole Error: {}'.format(import_error))
    from PyQt4.QtGui import QApplication


def test_archive_single_run(command_tester):
    """
    test viewing data from archive with multiple reduced runs
    :return:
    """
    command_line = 'VIEW,IPTS=22126,RUNS=171899'
    command_tester.run_command(command_line)

    return


def test_case_archive_chopped(command_tester):
    """
    test viewing data from archive with chopped and focused run
    :param command_tester:
    :return:
    """
    command_line = 'view,IPTS=22126,choprun=171899, runs=1, rune=15'
    command_tester.run_command(command_line)

    return


def test_case_archive_chopped_pc(command_tester):
    """
    test viewing data from archive with chopped and focused run
    :param command_tester:
    :return:
    """
    command_line = 'view,IPTS=22126,choprun=171899,runs=1,rune=15,norm=1,minv=1.0,maxv=2.0'
    command_tester.run_command(command_line)

    return


def test_case_archive_chopped_van(command_tester):
    """
    test viewing data from archive with chopped and focused run
    :param command_tester:
    :return:
    """
    command_line = 'view,IPTS=22126,choprun=171899, runs=1, rune=10, runv=163021,'
    command_tester.run_command(command_line)

    return

def test_case_archive_single_normalize(command_tester):
    """
    test viewing data from archive with single run in a specified d-spacing range and be normalized
    :param command_tester:
    :return:
    """
    command_line = 'VIEW,IPTS=22126,RUNS=171899,MINV=0.5,MAXV=2.5,NORM=1, runv=163021'
    command_tester.run_command(command_line)

    return


def test_case_reduce_view(command_tester):
    """
    test viewing data from a just-reduced run
    :param command_tester:
    :return:
    """
    # bin
    command_line = 'VBIN,IPTS=13183,RUNS=68607'
    command_tester.run_command(command_line)

    # view
    command_line = 'VIEW,IPTS=13183,RUNS=68607'
    command_tester.run_command(command_line)

    return


def test_case_chop_focus_view(command_tester):
    """
    test viewing data from a just-chopped-focused run
    :param command_tester:
    :return:
    """
    # chop and focus
    command_line = 'CHOP, IPTS=????, RUNS=????, TIME=5'
    command_tester.run_command(command_line)

    # view
    command_line = 'VIEW,IPTS=????, RUNS=????'
    command_tester.run_command(command_line)

    return


def test_main():
    """
    test main for command VIEW
    """
    Passed = False
    Next = False
    Now = True

    command_tester = command_test_setup.PyVdriveCommandTestEnvironment()

    if Now:
        test_archive_single_run(command_tester)
        test_case_archive_chopped_pc(command_tester)

    if Passed:
        # no need to test now
        test_archive_single_run(command_tester)
        test_case_archive_chopped(command_tester)
        test_case_archive_chopped_van(command_tester)
        test_case_archive_single_normalize(command_tester)
        pass

    if Next:
        pass 


    # test_case_archive(command_tester)
    #
    # test_case_archive_chopped(command_tester)
    #
    #
    # test_case_reduce_view(command_tester)
    #
    # test_case_chop_focus_view(command_tester)

    return command_tester.main_window


def main(argv):
    """ main to define QApplication
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

    app.exec_()


