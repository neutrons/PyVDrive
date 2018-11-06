#!/usr/bin/python
from pyvdrive.app import collimator_analysis
from matplotlib import pyplot as plt


if False:
    state, collimator = collimator_analysis.scan_rotating_collimator(ipts=20280,
                                                                     runs='tests/data/collimator_runs.txt',
                                                                     pixels='tests/data/collimator_roi.txt',
                                                                     to_focus=True)

    data_set = collimator.get_output_data()

    run_numbers = data_set.keys()
    for run_number in run_numbers:
        vec_x, vec_y = data_set[run_number]
        plt.plot(vec_x[:-1], vec_y)
# ENDIF

if True:
    state, collimator = collimator_analysis.scan_detector_column(ipts=20280, base_run=1234, target_run=2345)
    if state:
        data_set = collimator.get_output_data()
        for run_number in data_set.keys():
            vec_x, vec_y = data_set[run_number]
            plt.plot(vec_x[:-1], vec_y)
    else:
        err_msg = collimator
        print ('Failed to calculate 2theta-detector counts due to {}'.format(err_msg))


plt.show()
