#!/usr/bin/python
# Test the chop and reduce command
import os
import sys
import command_test_setup
try:
    from PyQt5.QtWidgets import QApplication
except ImportError as import_error:
    print ('[ild_vbin_test] Import PyQt5/qtconsole Error: {}'.format(import_error))
    from PyQt4.QtGui import QApplication


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

    # do test
    test_file = os.path.join(test_dir, '169186.gda')
    gold_file = '/SNS/VULCAN/IPTS-20280/shared/binned_data/169186.gda'
    tester.examine_result([test_file], [gold_file])

    return


def test_ned_multiple_runs(tester):
    """ Test the mode simple reduction case for data collected by nED
    :param tester:
    :return:
    """
    # test directory
    test_dir = '/tmp/vbin_ned_mulruns'
    command_test_setup.set_test_dir(test_dir)

    # run command
    idl_command = "VBIN,IPTS=20280,RUNS=169186,RUNE=169189,output=\'{}\'".format(test_dir)
    tester.run_command(idl_command)

    # output summary
    tester.show_output_files(test_dir)

    # do test
    test_files = list()
    gold_files = list()
    for run_number in range(169186, 169189+1):
        file_name_i = os.path.join(test_dir, '{}.gda'.format(run_number))
        gold_file_i = '/SNS/VULCAN/IPTS-20280/shared/binned_data/{}.gda'.format(run_number)
        test_files.append(file_name_i)
        gold_files.append(gold_file_i)
    # END-FOR
    tester.examine_result(test_files, gold_files)

    return


def test_ned_runv(tester):
    """ Test the mode simple reduction case for data collected by nED
    :param tester:
    :return:
    """
    # test directory
    test_dir = '/tmp/vbin_ned_runv'
    command_test_setup.set_test_dir(test_dir)

    # run command
    idl_command = "VBIN,IPTS=20280,RUNS=169186,runv=163021,output=\'{}\'".format(test_dir)
    tester.run_command(idl_command)

    # output summary
    tester.show_output_files(test_dir)

    # # do verification by examine value
    # test_file = os.path.join(test_dir, '169186.gda')
    #
    # # exists?
    # if not os.path.exists(test_file):
    #     tester.set_failure('Command "{}" failed: output file {} cannot be found.'
    #                        ''.format(idl_command, test_file))
    # else:
    #     all_one = verify_all_one_gsas(test_file)
    #     if all_one:
    #         tester.set_success('Command "{}" is executed successfully'.format(idl_command))
    #     else:
    #         tester.set_failure('Command "{}" failed: output GSAS {} does not have uniform Y=1'
    #                            ''.format(idl_command, test_file))

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
    idl_command = "VBIN,IPTS=20280,RUNS=169186,tag='SiTest',tagdir='/tmp',output=\'{}\'".format(test_dir)
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
    idl_command = "VBIN,IPTS=20280,RUNS=169186,binw=0.0005, Mytofmin=6000.," \
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


def test_ned_single_mask(tester):
    """
    Test binning with single mask
    :param tester:
    :return:
    """
    # test directory
    test_dir = '/tmp/vbin_ned_mask'
    command_test_setup.set_test_dir(test_dir)

    # this shall be a failed command
    idl_command = 'VBIN,IPTS=20280,RUNS=169187,output=\'{}\',' \
                  'mask=[tests/data/mask169186b3.xml]'.format(test_dir)
    tester.run_command(idl_command)

    # output summary
    tester.show_output_files(test_dir)
    # do test
    test_file = os.path.join(test_dir, '169187.gda')
    gold_file = '/SNS/VULCAN/IPTS-20280/shared/binned_data/169186.gda'

    'VULCAN_calibrate_2018_06_013banks'

    tester.examine_result([test_file], [gold_file])

    return


def test_ned_multiple_masks(tester):
    """
    Test binning with single mask
    :param tester:
    :return:
    """
    # test directory
    test_dir = '/tmp/vbin_ned_2masks'
    command_test_setup.set_test_dir(test_dir)

    # this shall be a failed command
    idl_command = 'VBIN,IPTS=20280,RUNS=169187,output=\'{}\',' \
                  'mask=[tests/data/mask169186b1.xml, tests/data/mask169186b3.xml]'.format(test_dir)
    tester.run_command(idl_command)

    # output summary
    tester.show_output_files(test_dir)
    # do test
    test_file = os.path.join(test_dir, '169187.gda')
    gold_file = '/SNS/VULCAN/IPTS-20280/shared/binned_data/169186.gda'

    tester.examine_result([test_file], [gold_file])

    return


def test_ned_multi_roi(tester):
    """
    Test binning with region of interest
    :param tester:
    :return:
    """
    # test directory
    test_dir = '/tmp/vbin_ned_rois'
    command_test_setup.set_test_dir(test_dir)

    # this shall be a failed command
    idl_command = 'VBIN,IPTS=20280,RUNS=169186,output=\'{}\',' \
                  'roi=[tests/data/roi169186b2.xml, tests/data/roi169186b3.xml]'.format(test_dir)
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

    # simple test with 1 run
    #test_ned_simple(command_tester)

    ## test with user defined binning of 1 run
    #test_ned_user_bin(command_tester)

    ## test with multiple runs
    #test_ned_multiple_runs(command_tester)

    ## test with various grouping
    #test_ned_multi_banks(command_tester)

    ## test single mask
    #test_ned_single_mask(command_tester)

    ## test multiple (2) masks
    #test_ned_multiple_masks(command_tester)

    ## test multiple (2) ROI
    #test_ned_multi_roi(command_tester)

    # test RUNV
    # test_ned_runv(command_tester)

    # test for standard material (Si, C, ...)
    test_ned_standard(command_tester)

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

