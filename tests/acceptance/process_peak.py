import pytest
import os
import pyvdrive.core.mantid_helper as mantid_helper
import pyvdrive.core.VDriveAPI as vdapi


def init_background():
    """
    Import packages

    Note: No print will be directed to terminal.  But the method is executed.
    """
    return


def init_test():
    """ Intialize the test including
    """
    print('Test case: IPTS 13587  Run 70269 for silicon. FCC a=b=c=5.43, F d 3 m')
    print('Test case: IPTS 13587  Run 66623 for unknown FCC material')

    return


def calculate_reflections():
    """ Set up IPTS, run number and etc for reduction
    """
    silicon = mantid_helper.UnitCell(mantid_helper.UnitCell.FC, 5.43)  # 5.43, 5.43
    reflections = mantid_helper.calculate_reflections(silicon, 1.0, 5.0)

    num_ref = len(reflections)
    ref_dict = dict()
    for i_ref in range(num_ref):
        ref_tup = reflections[i_ref]
        pos_d = ref_tup[1]
        hkl = ref_tup[0]
        if pos_d not in ref_dict:
            ref_dict[pos_d] = list()
        ref_dict[pos_d].append(hkl)

    pos_d_list = ref_dict.keys()
    pos_d_list.sort(reverse=True)

    return


def reduce_silicon():
    """ Reduce a silicon run
    :return:
    """
    work_flow = vdapi.VDriveAPI('VULCAN')
    archive_root = '/SNS/VULCAN'
    work_flow.set_data_root_directory(archive_root)
    work_flow.set_working_directory('~/Temp/VDriveTest/')

    ipts_number = 13587
    work_flow.set_ipts(ipts_number)
    status, run_tup_list = work_flow.get_ipts_info(ipts_number)
    assert status

    first_run = 70269
    last_run = 70269
    status, filter_run_tup_list = vdapi.filter_runs_by_run(run_tup_list, first_run, last_run)
    assert status
    assert len(filter_run_tup_list) == 1

    status, error_message = work_flow.add_runs_to_project(run_tup_list, ipts_number)
    assert status

    # Set reduction parameters
    focus_calib_file = '/SNS/VULCAN/shared/autoreduce/vulcan_foc_all_2bank_11p.cal'
    work_flow.set_focus_calibration_file(focus_calib_file)
    # set up reduction parameters
    output_dir = os.getcwd()
    reduction_param_dict = {
        "Extension": "_event.nxs",
        "PreserveEvents": True,
        "Binning": -0.001,
        "OutputDirectory": output_dir,
        "NormalizeByCurrent":  False,
        "FilterBadPulses": False,
        "CompressTOFTolerance": False,
        "FrequencyLogNames": "skf1.speed",
        "WaveLengthLogNames": "skf12.lambda",
    }
    work_flow.set_reduction_parameters(reduction_param_dict)

    # reduce
    # work_flow.set_runs_to_reduce(run_numbers=[27269])
    reduction_list = [(70269, True)]
    status, err_msg = work_flow.set_reduction_flag(file_flag_list=reduction_list, clear_flags=False)
    assert status, err_msg

    status, ret_obj = work_flow.reduce_data_set(norm_by_vanadium=False)
    print('[Message] ', str(ret_obj))
    assert status, ret_obj


if __name__ == '__main__':
    pytest.main(__file__)  # type: ignore
