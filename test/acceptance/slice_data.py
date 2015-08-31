from lettuce import *
from nose.tools import assert_equals, assert_true

import sys


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
    wk_flow = vdapi.VDriveAPI()
    wk_flow.set_data_root_directory('/Users/wzz/Projects/SNSData/VULCAN/')
    wk_flow.set_working_directory('~/Temp/VDriveTest/')

    my_data.set(wk_flow)

    wk_flow_2 = my_data.get()
    assert_true(wk_flow_2)

    return


@step(u'I get a list of runs from a local directory')
def setup_ipts(step):
    """ Set up IPTS, run number and etc for reduction
    """
    wk_flow = my_data.get()
    assert_true(wk_flow)

    # Set up IPTS
    ipts_dir = '/Users/wzz/Projects/SNSData/VULCAN/IPTS-10311-Local/'
    status, errmsg = wk_flow.set_ipts(ipts_dir)
    assert_true(status)

    # Get runs
    status, run_tup_list = wk_flow.get_ipts_info()
    assert_equals(status, True)
    assert_equals(len(run_tup_list), 4)

    my_data.set_ipts_runs(ipts_number, run_tup_list)

    return


@step(u'I filter the runs by run numbers')
def filter_runs(step):
    """ Filter runs by date
    """
    wk_flow = my_data.get()
    ipts_number, run_tup_list = my_data.get_ipts_runs()
    assert_equals(len(run_tup_list), 4)
    assert_equals(ipts_number, -1)

    start_run = 588478
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
    assert_equals(ipts_number, None)

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

    status, filename = wk_flow.save_session('test1234.xml')
    assert_true(status)
    assert_equals(filename, '/tmp/test1234.xml')


    return

@step(u'I create a new VDriveAPI project and load saved session file to it')
def load_session(step):
    """ Load session to a new workflow instance
    :param step:
    :return:
    """
    # Create a new workflow and load the file to the new workflow instance
    new_wk_flow = vdapi.VDriveAPI()
    saved_file_name = '/tmp/test1234.xml'
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

    # Get sample log names
    sample_log_names = wk_flow.get_sample_log_names()
    assert_true(test_sample_log_name in sample_log_names)

    # Get log data
    status, ret_obj = wk_flow.get_sample_log_values(test_sample_log_name)
    assert_true(status)
    vec_times, vec_value = ret_obj
    assert_equals(len(vec_times), 1000)
    assert_true(abs(vec_value[0] - 1234) < 1.0E-7)
    assert_true(abs(vec_value[-1] - 4567) < 1.0E-7)

    return
