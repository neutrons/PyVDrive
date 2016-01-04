from lettuce import *
from nose.tools import assert_equals, assert_true

import sys
import os
import os.path

# FIXME - This only works for Linux platform
sys.path.append('/home/wzz/local/lib/python2.7/Site-Packages/')
import PyVDrive.VDriveAPI as vdapi

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
ipts_number = 10311


@step(u'I am using VDriveAPI')
def init_workflow(step):
    """ Set up including
    """
    # We don't need this!

    return


@step(u'I get a list of runs belonged to an IPTS number')
def setup_ipts(step):
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
    assert_equals(status, True)
    assert_equals(len(run_tup_list), 1777)

    my_data.set_ipts_runs(ipts_number, run_tup_list)

    return


@step(u'I filter the runs by date')
def filter_runs(step):
    """ Filter runs by date
    """
    wk_flow = my_data.get()
    ipts_number, run_tup_list = my_data.get_ipts_runs()
    assert_equals(len(run_tup_list), 1777)

    start_date = '02/09/2015'
    end_date = '02/10/2015'
    status, filter_run_tup_list = vdapi.filter_runs_by_date(run_tup_list, start_date, end_date)
    assert_equals(status, True)
    assert_equals(len(filter_run_tup_list), 69)

    my_data.set_ipts_runs(ipts_number, filter_run_tup_list)

    return

@step(u'I input IPTS, run numbers')
def set_ipts_runs(step):
    """
    """
    wk_flow = my_data.get()
    ipts_number, run_tup_list = my_data.get_ipts_runs()

    status, error_message = wk_flow.clear_runs()
    assert_equals(status, True)

    status, error_message = wk_flow.add_runs(run_tup_list, ipts_number)
    assert_equals(status, True)
    assert_equals(69, wk_flow.get_number_runs())


    """
    # new project
    wkflow.newProject(projname = "Test001", projtype = "reduction")
    # set data path with default
    wkflow.setDataPath(projname = 'Test001')
    # IPTS and runs
    ipts = 10311
    runs= range(57070, 57078)

    # FIXME : Should be put to 2 different test cases in future
    if False:
        # Manual setup
        wkflow.setVanadiumFile('/SNS/VULCAN/shared/Calibrationfiles/Instrument/Standard/Vanadium/VRecord.txt')
        criterialist = [('Frequency', 'float'), ('Guide', 'float'), ('Collimator', 'float')]
        # set vanadium calibration (new project should add data and locate calibration file automatically)
        wkflow.setVanadiumCalibrationMatchCriterion('Test001', criterialist)
        # add experiment 
        status, errmsg, datafilesets = wkflow.addExperimentRuns('Test001', 'reduction', ipts, runs, True)

    else:
        # Automatic setup
        r = wkflow.addExperimentRuns(projname='Test001', operation='Add Experiment Runs', ipts=ipts, 
                runnumberlist=runs, autofindcal=True)
    # ENDIFELSE
    """

    return

@step(u'I save current session to a file')
def save_session(step):
    """ Save sessions
    """
    wk_flow = my_data.get()
    assert(isinstance(wk_flow, vdapi.VDriveAPI))

    status, filename = wk_flow.save_session('test1234.xml')
    work_dir = wk_flow.get_working_dir()
    assert_true(status)
    assert_equals(filename, os.path.join(work_dir, 'test1234.xml'))

    return


@step(u'I create a new VDriveAPI project and load saved session file to it')
def load_session(step):
    """ Load session to a new workflow instance
    :param step:
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
    assert_equals(wk_flow.get_number_runs(), new_wk_flow.get_number_runs())
    assert_equals(wk_flow.get_working_dir(), new_wk_flow.get_working_dir())

    return


@step(u'Then I add add a run number to the VDrive project for reduction')
def add_run_to_reduce(step):
    """ Add a run to reduce
    :param step:
    :return:
    """
    workflow = my_data.get()

    workflow.set_runs_to_reduce(run_numbers=[57072])

    return

@step(u'Then I reduce the data')
def reduce_data(step):
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
        "Binning" : -0.001,
        "OutputDirectory" : outputdir,
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
    print\
        '[Message] ', str(ret_obj)
    print
    assert_true(status, str(ret_obj))

    return

@step(u'Then I check a matrix workspace generated from that run')
def retrieve_reduced_data(step=9):
    """ Test retrieve reduced data
    :param step:
    :return:
    """
    # Get workflow
    work_flow = my_data.get()

    reduced_run_list = work_flow.get_reduced_runs()
    num_reduced_runs = len(reduced_run_list)
    assert_equals(num_reduced_runs, 1)
    status, reduced_data = work_flow.get_reduced_data(reduced_run_list[0], 'dspace')
    assert_true(status)
    assert_true(isinstance(reduced_data, dict))
    assert_equals(len(reduced_data.keys()), 2)
    assert_equals(len(reduced_data), 2)
    assert_equals(len(reduced_data[0]), 3)


@step(u'Reduce 2 runs and check results')
def reduce_2_runs(step=10):
    """ Test to reduce multiple runs
    :param step:
    :return:
    """
    # Get workflow
    work_flow = my_data.get()

if __name__ == "__main__":

    if False:
        init_workflow(1)
        setup_ipts(2)
        filter_runs(3)
        set_ipts_runs(4)
        save_session(5)
        load_session(6)
        add_run_to_reduce(7)
        reduce_data(8)
        retrieve_reduced_data(9)

