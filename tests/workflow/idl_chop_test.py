#!/usr/bin/python
# Test the chop and reduce command
import sys
import os
# create main application
import command_test_setup

try:
    from PyQt5.QtWidgets import QApplication
except ImportError:
    from PyQt4.QtGui import QApplication


def create_slice_segment_file(test_dir):
    """
    create a slice segment file on the fly
    :param test_dir:
    :return:
    """
    file_name = os.path.join(test_dir, 'slice_segment.txt')

    segment = '0.   50.\n51.     150.\n155.     300'

    segment_file = open(file_name, 'w')
    segment_file.write(segment)
    segment_file.close()

    return file_name


def test_chop_simple(tester):
    """
    /SNS/VULCAN/IPTS-20717/nexus/VULCAN_170464.nxs.h5
    :param tester:
    :return:
    """
    # test directory
    test_dir = '/tmp/chop_simple'
    command_test_setup.set_test_dir(test_dir)

    # run command
    idl_command = 'chop, ipts=20717, runs=170464, dbin=300, loadframe=1, output="{}"'.format(test_dir)

    tester.run_command(idl_command)

    # output summary
    tester.show_output_files(test_dir)

    return


def test_chop_van_normalized(tester):
    """
    chop with vanadium run (vrun)
    :param tester:
    :return:
    """
    # test directory
    test_dir = '/tmp/chop_vrun'
    command_test_setup.set_test_dir(test_dir)

    # run command
    idl_command = 'chop, ipts=20717, runs=170464, dbin=300, loadframe=1, ' \
                  'runv=163021,output="{}"'.format(test_dir)

    tester.run_command(idl_command)

    # output summary
    tester.show_output_files(test_dir)

    return


def test_chop_analysis_cluster(tester):
    """
    chop with vanadium run (vrun)
    :param tester:
    :return:
    """
    # test directory
    test_dir = '/SNS/VULCAN/IPTS-20717/shared/binned_data/170464'
    command_test_setup.set_test_dir(test_dir)

    # run command
    idl_command = 'chop, ipts=20717, runs=170464, dbin=30, loadframe=1, ' \
                  'runv=163021,starttime=10.,stoptime=250.'

    tester.run_command(idl_command)

    # output summary
    tester.show_output_files(test_dir)

    return


def test_chop_overlap_time(tester):
    """
    /SNS/VULCAN/IPTS-20717/nexus/VULCAN_170464.nxs.h5
    :param tester:
    :return:
    """
    # test directory
    test_dir = '/tmp/chop_overlap_time'
    command_test_setup.set_test_dir(test_dir)

    # run command
    idl_command = 'chop, ipts=20717, runs=170464, dbin=100, dt=20, loadframe=1, output="{}"'.format(test_dir)

    tester.run_command(idl_command)

    # output summary
    tester.show_output_files(test_dir)

    return


def test_chop_roi(tester):
    """
    chop with ROI specified
    :param tester:
    :return:
    """
    # test directory
    test_dir = '/tmp/chop_multiple_roi'
    command_test_setup.set_test_dir(test_dir)

    # run command
    idl_command = 'chop, ipts=20717, runs=170464, dbin=300, loadframe=1,' \
                  'roi=[tests/data/roi169186b2.xml, tests/data/roi169186b3.xml],' \
                  'BinFolder="{}"'.format(test_dir)

    tester.run_command(idl_command)

    # output summary
    tester.show_output_files(test_dir)


def test_chop_segment_file(tester):
    """

    :param tester:
    :return:
    """
    # test directory
    test_dir = '/tmp/chop_segment_file'
    command_test_setup.set_test_dir(test_dir)

    # create file
    seg_fie_name = create_slice_segment_file(test_dir)

    # run command
    idl_command = 'chop, ipts=20717, runs=170464,  PICKDATA={}, loadframe=1, binfolder="{}"' \
                  ''.format(seg_fie_name, test_dir)

    tester.run_command(idl_command)

    # output summary
    tester.show_output_files(test_dir)

    return


def test_pre_ned(command_tester):
    """
    """
    # regular run for functionality test
    chop_cmd01 = "CHOP, IPTS=13924, RUNS=160989, dbin=60,loadframe=1,bin=1,DRYRUN=0, output='/tmp/'"
    command_tester.run_command(chop_cmd01)

    return


def performance_test_ned_12_hour(tester):
    """
    """
    # nED 12 hour run for performance test
    test_dir = '/tmp/chop_test_12hour/'
    tester.set_test_dir(test_dir)

    idl_command = "CHOP, IPTS=19290, RUNS=156378, dbin=60,loadframe=1,bin=1,DRYRUN=0, output={}".format(test_dir)
    tester.run_command(idl_command)

    # output summary
    tester.show_output_files(test_dir)

    return


def test_ned_12_hour_segment_file(tester):
    """
    Test chop a 12 hour run by segment file
    :param tester:
    :return:
    """
    # set up the testing diretory
    test_dir = '/tmp/pyvdrive_chop_12h_segfile'
    tester.set_test_dir(test_dir)

    # get the sample segment file
    segment_file_name = create_slice_segment_file(test_dir)

    # run VDRIVE command
    command = "CHOP,  IPTS=20280, RUNS=169173, DBIN=300, PICKDATA={}, OUTPUT='{}".format(segment_file_name, test_dir)
    tester.run_command(command)

    # show summary
    tester.show_output_files(test_dir)

    return


def test_performance_pre_ned_10hour(command_tester):
    """
    """
    # preNED 10 hour run for performance test
    chop_cmd03 = "CHOP, IPTS=13924, RUNS=142777, dbin=60,loadframe=1,bin=1,DRYRUN=0, output='/tmp/'"
    command_tester.run_command(chop_cmd01)


def test_last(command_tester):
    """
    """
    test_dir = '/tmp/choptest_X/'
    create_test_dir(test_dir)

    chop_cmd04 = "CHOP, IPTS=19577, RUNS=155771, dbin=60,loadframe=1,bin=1,DRYRUN=0, output='{}'".format(test_dir)
    command_tester.run_command(chop_cmd04)


def test_main():
    """
    test main
    """
    command_tester = command_test_setup.PyVdriveCommandTestEnvironment()

    # basic chopping operation
    test_chop_simple(command_tester)

    # # # chop with vanadium runs
    # test_chop_van_normalized(command_tester)

    # # # chop with mask/ROI
    # test_chop_roi(command_tester)

    # # chop with PICKDATA
    # test_chop_segment_file(command_tester)

    # chop with DT
    # test_chop_overlap_time(command_tester)

    # chop on analysis cluster
    # test_chop_analysis_cluster(command_tester)

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




# /SNS/VULCAN/IPTS-19577/nexus/VULCAN_155771.nxs.h5: Runtime = 251.323285103   Total output workspaces = 733
# Details for thread = 8:
# 	Loading  = 92.1773381233
# 	Chopping = 35.1145699024
# 	Focusing = 79.9583420753
# 	SaveGSS = 44.0730350018
# ********* SEGMENTATION FAULT *********

# /SNS/VULCAN/IPTS-19577/nexus/VULCAN_155771.nxs.h5: Runtime = 255.423187971   Total output workspaces = 733
# Details for thread = 16:
# 	Loading  = 91.5541679859
# 	Chopping = 35.390401125
# 	Focusing = 82.6177368164
# 	SaveGSS = 45.8608820438

# /SNS/VULCAN/IPTS-19577/nexus/VULCAN_155771.nxs.h5: Runtime = 256.438976049   Total output workspaces = 733
# Details for thread = 32:
# 	Loading  = 92.5543420315
# 	Chopping = 35.9679849148
# 	Focusing = 84.067358017
# 	SaveGSS = 43.8492910862


# /SNS/VULCAN/IPTS-19577/nexus/VULCAN_155771.nxs.h5: Runtime = 269.704912901   Total output workspaces = 733
# Details for thread = 12:
# 	Loading  = 91.6898329258
# 	Chopping = 35.2826209068
# 	Focusing = 97.724822998
# 	SaveGSS = 45.0076360703
