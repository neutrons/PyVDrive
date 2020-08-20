import pytest
import os
import os.path
import pyvdrive.lib.VDriveAPI as vdapi


class MyData:
    def __init__(self):
        """ Init
        """
        self.myObject = None
        self._ipts = None
        self._runs = []

    def __str__(self):
        """ Nice output
        """
        return str(self.myObject)

    def get(self):
        """ Get
        """
        return self.myObject

    def get_ipts_runs(self):
        """

        :return:
        """
        return self._ipts, self._runs[:]

    def set(self, inputobject):
        """ Set
        """
        if inputobject is None:
            raise NotImplementedError("Input object is not supposed to be None.")

        self.myObject = inputobject

        return

    def set_ipts_runs(self, ipts_number, run_tup_list):
        """
        Set up
        :param ipts_number:
        :param run_tup_list:
        :return:
        """
        self._ipts = int(ipts_number)
        self._runs = run_tup_list[:]
        assert(self._runs, list)


my_data = MyData()

# Global testing data
ipts_number = 16002


def init_workflow():
    """ Do nothing at all.  It is a given situation and it won't be called.
    """
    pass


def initialize_project():
    """
    Initialize the workflow instance and set up a reduction project
    :return:
    """
    # Initialize work flow
    wk_flow = vdapi.VDriveAPI('VULCAN')
    archive_root = '/SNS/VULCAN'
    if os.path.exists(archive_root) is False:
        archive_root = None
    wk_flow.set_data_root_directory(archive_root)
    wk_flow.set_working_directory('~/Temp/VDriveTest/')

    # Set to my_data
    my_data.set(wk_flow)

    return


def setup_ipts():
    """ Set up IPTS, run number and etc for reduction
    """
    # Get workflow
    wk_flow = my_data.get()

    # Set up IPTS
    assert ipts_number is not None
    wk_flow.set_ipts(ipts_number)

    # Get runs
    status, run_tup_list = wk_flow.get_ipts_info(ipts_number)
    assert status

    my_data.set_ipts_runs(ipts_number, run_tup_list)

    return


def filter_runs_by_run():
    """ Filter runs by date
    """
    this_ipts_number, run_tup_list = my_data.get_ipts_runs()

    first_run = 80230
    last_run = 80240
    status, filter_run_tup_list = vdapi.filter_runs_by_run(run_tup_list, first_run, last_run)
    assert len(filter_run_tup_list) == 10

    my_data.set_ipts_runs(ipts_number, filter_run_tup_list)

    return


def set_ipts_runs():
    """
    """
    wk_flow = my_data.get()
    this_ipts_number, run_tup_list = my_data.get_ipts_runs()

    status, error_message = wk_flow.clear_runs()
    assert status

    status, error_message = wk_flow.add_runs_to_project(run_tup_list, this_ipts_number)
    assert status
    assert 10 == wk_flow.get_number_runs()


def add_run_to_reduce():
    """ Add a run to reduce
    :return:
    """
    workflow = my_data.get()

    workflow.set_runs_to_reduce(run_numbers=[80231])

    return


def reduce_single_set_data():
    """ Set up reduction parameter and reduce data
    """
    workflow = my_data.get()

    # Set reduction parameters
    focus_calib_file = '/SNS/VULCAN/shared/autoreduce/vulcan_foc_all_2bank_11p.cal'

    workflow.set_focus_calibration_file(focus_calib_file)

    # set up reduction parameters
    outputdir = os.getcwd()
    paramdict = {
        "Extension": "_event.nxs",
        "PreserveEvents": True,
        "Binning": -0.001,
        "OutputDirectory": outputdir,
        "NormalizeByCurrent":  False,
        "FilterBadPulses": False,
        "CompressTOFTolerance": False,
        "FrequencyLogNames": "skf1.speed",
        "WaveLengthLogNames": "skf12.lambda",
    }

    workflow.set_reduction_parameters(paramdict)

    # reduce
    reduction_list = [(80231, True)]
    workflow.set_reduction_flag(file_flag_list=reduction_list, clear_flags=True)

    status, ret_obj = workflow.reduce_data_set(norm_by_vanadium=False)
    print('[Message] ', str(ret_obj))
    assert status


def export_to_gsas():
    """ Test retrieve reduced data
    :return:
    """
    # Get workflow
    work_flow = my_data.get()

    output_file_name = '/tmp/acceptance_test.gda'

    # Clear the file if it exists.
    if os.path.exists(output_file_name):
        os.remove(output_file_name)

    status = work_flow.export_gsas_file(run_number=80231)
    assert status
    assert os.path.exists(output_file_name)


# TODO/NOW/1st: Think of some crazy things to process the reduced data such as normalize by current, 
# change unit, and etc.


if __name__ == "__main__":

    init_workflow()
    initialize_project()
    setup_ipts()
    filter_runs_by_run()
    set_ipts_runs()
    add_run_to_reduce()
    reduce_single_set_data()
    export_to_gsas()
