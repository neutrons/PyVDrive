from lettuce import *
from nose.tools import assert_equals, assert_true, assert_false

import sys
import os


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


my_data = MyData()


@step(u'I am using VDriveAPI')
def init_workflow(step):
    """ Set up including
    """
    assert_equals(1, 4)
    wk_flow = vdapi.VDriveAPI()
    assert_equals(1, 2)
    wk_flow.set_data_root_directory('/Users/wzz/Projects/SNSData/VULCAN/')
    # Test to use ~/ in given directory
    wk_flow.set_working_directory('~/Temp/VDriveTest/')
    my_data.set(wk_flow)

    return


@step(u'I get a list of runs from a local directory')
def setup_ipts(step):
    """ Set up IPTS, run number and etc for reduction
    """
    wk_flow = vdapi.VDriveAPI()
    wk_flow.set_data_root_directory('/Users/wzz/Projects/SNSData/VULCAN/')
    # Test to use ~/ in given directory
    wk_flow.set_working_directory('~/Temp/VDriveTest/')
    my_data.set(wk_flow)

    wk_flow = my_data.get()
    assert_true(wk_flow is not None)

    # Set up IPTS
    ipts_dir = os.path.expanduser('~/Projects/SNSData/VULCAN/IPTS-10311-Local/')
    status, errmsg = wk_flow.set_ipts(ipts_dir)
    assert_false(status)

    # Get runs
    status, run_tup_list = wk_flow.get_ipts_info(ipts_dir)
    assert_true(status)
    assert_equals(len(run_tup_list), 4)

    my_data.set_ipts_runs(-1, run_tup_list)

    return


@step(u'I filter the runs by run numbers')
def filter_runs(step):
    """ Filter runs by date
    """
    ipts_number, run_tup_list = my_data.get_ipts_runs()
    assert_equals(len(run_tup_list), 4)
    assert_equals(ipts_number, -1)

    start_run = 58848
    end_run = 58850
    status, filter_run_tup_list = vdapi.filter_runs_by_run(run_tup_list, start_run, end_run)
    assert_equals(status, True)
    assert_equals(len(filter_run_tup_list), 2)

    my_data.set_ipts_runs(ipts_number, filter_run_tup_list)

    return

@step(u'I input run number')
def set_ipts_runs(step):
    """
    Add runs to
    :param step:
    :return:
    """
    wk_flow = my_data.get()
    ipts_number, run_tup_list = my_data.get_ipts_runs()
    assert_equals(ipts_number, -1)

    status, error_message = wk_flow.clear_runs()
    assert_equals(status, True)

    status, error_message = wk_flow.add_runs(run_tup_list, ipts_number)
    assert_equals(status, True)
    assert_equals(2, wk_flow.get_number_runs())

    return

@step(u'I save current session to a file')
def save_session(step):
    """ Save sessions
    """
    wk_flow = my_data.get()
    assert(isinstance(wk_flow, vdapi.VDriveAPI))

    status, filename = wk_flow.save_session('test2345.xml')
    work_dir = wk_flow.get_working_dir()
    assert_true(status)
    assert_equals(work_dir, os.path.expanduser('~/Temp/VDriveTest/'))
    assert_equals(filename, os.path.join(work_dir, 'test2345.xml'))

    return

@step(u'I create a new VDriveAPI project and load saved session file to it')
def load_session(step):
    """ Load session to a new workflow instance
    :param step:
    :return:
    """
    # Create a new workflow and load the file to the new workflow instance
    new_wk_flow = vdapi.VDriveAPI()
    saved_file_name = os.path.join(new_wk_flow.get_working_dir, 'test2345.xml')
    new_wk_flow.load_session(saved_file_name)

    # Compare the new workflow and old one
    wk_flow = my_data.get()
    assert(isinstance(wk_flow, vdapi.VDriveAPI))

    assert_equals(wk_flow.get_number_runs(), new_wk_flow.get_number_runs())
    assert_equals(wk_flow.get_working_dir(), new_wk_flow.get_working_dir())

    return

@step(u'I input name of a sample log to get its data')
def input_sample_log_name(step):
    """
    Input a sample log's name and get it data
    :param step:
    :return:
    """
    # Get workflow
    wk_flow = my_data.get()
    assert(isinstance(wk_flow, vdapi.VDriveAPI))

    # Set up log file helper
    test_run_number = 58848
    test_sample_log_name = 'loadframe.stress'
    file_name = wk_flow.get_file_by_run(test_run_number)
    assert_equals(os.path.basename(file_name), 'VULCAN_58848_event.nxs')

    wk_flow.init_slicing_helper(file_name)

    # Get sample log names
    status, sample_log_names = wk_flow.get_sample_log_names()
    assert_true(status)
    assert_true(test_sample_log_name in sample_log_names)

    # Get log data
    status, ret_obj = wk_flow.get_sample_log_values(test_sample_log_name)
    assert_true(status)
    vec_times, vec_value = ret_obj
    assert_equals(len(vec_times), 205)
    assert_true(abs(vec_value[0] - -8.980486000000001) < 1.0E-7)
    assert_true(abs(vec_value[-1] - -9.243161000000001) < 1.0E-7)

    return
