import pytest
import os
import os.path
import pyvdrive.core.VDriveAPI as vdapi


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
        assert isinstance(self._runs, list)


my_data = MyData()

# Global testing data
ipts_number = 10311


def init_workflow():
    """ Set up including
    """
    # We don't need this!

    return


def setup_ipts():
    """ Set up IPTS, run number and etc for reduction
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

    wk_flow = my_data.get()

    # Set up IPTS
    assert ipts_number is not None
    wk_flow.set_ipts(ipts_number)

    # Get runs
    status, run_tup_list = wk_flow.get_ipts_info(ipts_number)
    assert status
    assert len(run_tup_list) == 1777

    my_data.set_ipts_runs(ipts_number, run_tup_list)

    return


def filter_runs():
    """ Filter runs by date
    """
    ipts_number, run_tup_list = my_data.get_ipts_runs()
    assert len(run_tup_list) == 1777

    start_date = '02/09/2015'
    end_date = '02/10/2015'
    status, filter_run_tup_list = vdapi.filter_runs_by_date(run_tup_list, start_date, end_date)
    assert status
    assert len(filter_run_tup_list) == 69

    my_data.set_ipts_runs(ipts_number, filter_run_tup_list)

    return


def set_ipts_runs():
    """
    """
    wk_flow = my_data.get()
    ipts_number, run_tup_list = my_data.get_ipts_runs()

    status, error_message = wk_flow.clear_runs()
    assert status

    status, error_message = wk_flow.add_runs_to_project(run_tup_list, ipts_number)
    assert status, True
    assert 69 == wk_flow.get_number_runs()


def save_session():
    """ Save sessions
    """
    wk_flow = my_data.get()
    assert(isinstance(wk_flow, vdapi.VDriveAPI))

    status, filename = wk_flow.save_session('test1234.xml')
    work_dir = wk_flow.get_working_dir()
    assert status
    assert filename == os.path.join(work_dir, 'test1234.xml')


def load_session():
    """ Load session to a new workflow instance
    :return:
    """
    # Current workflow
    wk_flow = my_data.get()
    assert(isinstance(wk_flow, vdapi.VDriveAPI))

    # Create a new workflow and load the file to the new workflow instance
    new_wk_flow = vdapi.VDriveAPI('vulcan')

    saved_file_name = os.path.join(wk_flow.get_working_dir(), 'test1234.xml')
    new_wk_flow.load_session(saved_file_name)

    # Compare the new workflow and old one
    assert wk_flow.get_number_runs() == new_wk_flow.get_number_runs()
    assert wk_flow.get_working_dir() == new_wk_flow.get_working_dir()


def add_run_to_reduce():
    """ Add a run to reduce
    :return:
    """
    workflow = my_data.get()

    workflow.set_runs_to_reduce(run_numbers=[57072])

    return


def reduce_data():
    """ Set up reduction parametera and reduce data
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
    reduction_list = [(58802, True)]
    workflow.set_reduction_flag(file_flag_list=reduction_list, clear_flags=True)

    status, ret_obj = workflow.reduce_data_set(norm_by_vanadium=False)
    print('[Message] ', str(ret_obj))
    assert status == str(ret_obj)


def retrieve_reduced_data():
    """ Test retrieve reduced data
    :return:
    """
    # Get workflow
    work_flow = my_data.get()

    reduced_run_list = work_flow.get_reduced_runs()
    num_reduced_runs = len(reduced_run_list)
    assert num_reduced_runs == 1
    status, reduced_data = work_flow.get_reduced_data(reduced_run_list[0], 'dspace')
    assert status
    assert isinstance(reduced_data, dict)
    assert len(reduced_data.keys()) == 2
    assert len(reduced_data) == 2
    assert len(reduced_data[0]) == 3


def reduce_2_runs():
    """ Test to reduce multiple runs
    :return:
    """
    # Get workflow
    work_flow = my_data.get()
    assert work_flow


def test_workflow():
    init_workflow()
    setup_ipts()
    filter_runs()
    set_ipts_runs()
    save_session()
    load_session()
    add_run_to_reduce()
    reduce_data()
    retrieve_reduced_data()


if __name__ == "__main__":
    pytest.main(__file__)  # type: ignore
