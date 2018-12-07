#!/usr/bin/python
from pyvdrive.app import collimator_analysis
from matplotlib import pyplot as plt
from matplotlib import legend
import os
import sys
from numpy import arange,sqrt


def check_out_file_name(output_name):
    dir_name = os.path.dirname(output_name)
    if os.path.exists(dir_name) is False or os.access(dir_name, os.W_OK) is False:
        print ('Directory {} either does not exist or is not writable.'.format(dir_name))
        sys.exit(1)


if True:
    # sum spectra for a set of runs
    # output file name
    out_file_name = '/SNS/VULCAN/shared/PyVDrive/temp01.dat'
    out_file_name = '/tmp/temp01.dat'
    check_out_file_name(out_file_name)

    state, collimator = collimator_analysis.scan_rotating_collimator(ipts=21356,
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
	i = float(sum(vec_y))
        plt.plot(vec_x, vec_y/i)
    plt.legend(run_numbers)
    plt.xlabel("TOF (microseconds)")
    plt.ylabel("Counts")
# ENDIF

if False:
    # sum counts along tube
    # output file name
    out_file_name = '/SNS/VULCAN/shared/PyVDrive/temptube169146.dat'
    out_file_name = '/tmp/temptube.dat'
    
    base_runnum = 169192
    compare_runnum = arange(169207,169208)
    
    check_out_file_name(out_file_name)

    state_base, collimator_base = collimator_analysis.scan_detector_column(ipts=21356, run_number=base_runnum)

    for i in compare_runnum:

            state_comp, collimator_comp = collimator_analysis.scan_detector_column(ipts=21356, run_number=i)

	    if state_base*state_comp:
		data_set_base = collimator_base.get_output_data()
		data_set_comp = collimator_comp.get_output_data()
		signal = data_set_comp[:, 1]/data_set_base[:,1]
		error = signal/sqrt(data_set_comp[:,1])
		plt.errorbar(data_set_base[::-1, 0], signal[::-1],error[::-1])
		plt.axis([156,144,None,None])
	    else:
		err_msg = collimator_base
		print ('Failed to calculate 2theta-detector counts due to {}'.format(err_msg))

	    # save to ASCII
	    collimator_comp.save_to_ascii(out_file_name)
    plt.xlabel("2Theta")
    plt.ylabel("Intensity Relative to %d"%base_runnum)
    plt.legend(tuple(compare_runnum))
plt.show()
