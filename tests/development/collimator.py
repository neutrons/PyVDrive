#!/usr/bin/python
from pyvdrive.app import collimator_analysis
from matplotlib import pyplot as plt
import os
import sys


def check_out_file_name(output_name):
    dir_name = os.path.dirname(output_name)
    if os.path.exists(dir_name) is False or os.access(dir_name, os.W_OK) is False:
        print ('Directory {} either does not exist or is not writable.'.format(dir_name))
        sys.exit(1)


if False:
    # sum spectra for a set of runs
    # output file name
    out_file_name = '/SNS/VULCAN/shared/PyVDrive/temp01.dat'
    out_file_name = '/tmp/temp01.dat'
    check_out_file_name(out_file_name)

    state, collimator = collimator_analysis.scan_rotating_collimator(ipts=20280,
                                                                     runs='tests/data/collimator_runs.txt',
                                                                     pixels='tests/data/collimator_roi.txt',
                                                                     to_focus=True)

    # save to ASCII
    collimator.save_to_ascii(out_file_name)

    # plot
    data_set = collimator.get_output_data()

    run_numbers = data_set.keys()
    for run_number in run_numbers:
        vec_x, vec_y = data_set[run_number]
        plt.plot(vec_x, vec_y)
# ENDIF

if True:
    # sum counts along tube
    # output file name
    out_file_name = '/SNS/VULCAN/shared/PyVDrive/temptube169146.dat'
    out_file_name = '/tmp/temptube.dat'
    check_out_file_name(out_file_name)

    state, collimator = collimator_analysis.scan_detector_column(ipts=20280, run_number=169146)
    if state:
        data_set = collimator.get_output_data()
        plt.plot(data_set[:, 0], data_set[:, 1])
    else:
        err_msg = collimator
        print ('Failed to calculate 2theta-detector counts due to {}'.format(err_msg))

    # save to ASCII
    collimator.save_to_ascii(out_file_name)


plt.show()
