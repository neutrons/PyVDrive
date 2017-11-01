from lettuce import *
from nose.tools import assert_equals, assert_true, assert_false

import sys
import os


# FIXME - This only works for Linux/MacOS X platform
sys.path.append('/home/wzz/local/lib/python2.7/Site-Packages/')
import PyVDrive.lib.VDriveAPI as vdapi

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


def getPyDriveDataDir(cwd):
    """
    """
    locate_it = False

    dir_in_process = cwd
    while locate_it is False:
        parent_dir, last_dir = os.path.split(dir_in_process)
        if last_dir.lower() == 'pyvdrive':
            locate_it = True
            data_dir = os.path.join(dir_in_process, 'test/data')
        elif parent_dir == '':
            raise RuntimeError('Unable to locate PyVDrive testing directory from %s.' % cwd)
        else:
            dir_in_process = parent_dir
    # END-WHILE()

    return data_dir

my_data = MyData()

@step(u'I am using VDriveAPI')
def init_workflow(step):
    """ Set up including
    Note: I really don't think this step does anything real.  It is skipped
    """
    print 'All Skipped'

    return


@step(u'I get a list of runs from a local directory')
def setup_ipts(step):
    """ Set up IPTS, run number and etc for reduction
    """
    # Set up workflow
    wk_flow = vdapi.VDriveAPI('VULCAN')

    # data source
    cwd = os.getcwd()
    # data_dir = getPyDriveDataDir(cwd)
    data_dir = '/SNS/VULCAN'
    print 'Data Dir: ', data_dir
    wk_flow.set_data_root_directory(data_dir)

    # work dir
    wk_dir = os.path.expanduser('~/Temp/VDriveTest/')
    wk_flow.set_working_directory(wk_dir)

    # Add workflow to my_data
    my_data.set(wk_flow)

    # Check whether my_data set up the workflow correct
    wk_flow = my_data.get()
    assert_true(wk_flow is not None)

    # Set up IPTS and expect 'false' result
    ipts_dir = os.path.join(data_dir, 'IPTS-10311')
    status, errmsg = wk_flow.set_ipts(10311)
    if not status:
        print '[ERROR]', errmsg
    assert_true(status)

    # Get runs from directory: get_ipts_info() is not used anymore
    # status, run_tup_list = wk_flow.get_ipts_info(ipts_dir)
    # assert_true(status)
    # assert_equals(len(run_tup_list), 4)

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

    status, error_message = wk_flow.add_runs_to_project(run_tup_list, ipts_number)
    assert_equals(status, True)
    assert_equals(2, wk_flow.get_number_runs())

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

    wk_flow.set_slicer_helper(file_name, test_run_number)

    # Get sample log names
    status, sample_log_names = wk_flow.get_sample_log_names()
    assert_true(status)
    assert_true(test_sample_log_name in sample_log_names)

    # Get log data
    status, ret_obj = wk_flow.get_sample_log_values(test_sample_log_name, relative=True)
    assert_true(status)
    vec_times, vec_value = ret_obj
    assert_equals(len(vec_times), 205)
    assert_true(abs(vec_value[0] - -8.980486000000001) < 1.0E-7)
    assert_true(abs(vec_value[-1] - -9.243161000000001) < 1.0E-7)

    return

@step(u'Then I set up rules to slice this run by this sample log and generate data slicer')
def generate_data_slicer(step):
    """
    Set up rules and create data slicer/event splitters by sample log value
    :param step:
    :return:
    """
    test_run_number = 58848
    test_log_name = 'loadframe.stress'

    # Get workflow
    wk_flow = my_data.get()
    assert(isinstance(wk_flow, vdapi.VDriveAPI))

    # Set up rule
    wk_flow.gen_data_slicer_sample_log(run_number=test_run_number,
                                       sample_log_name=test_log_name,
                                       start_time=1.0,
                                       end_time=200.1,
                                       min_log_value=-10.0,
                                       max_log_value=-8.0,
                                       log_value_step=1.0)

    return

@step(u'Then I slice data and check result')
def slice_data(step):
    """ Slice data by current splitters
    :param step:
    :return:
    """
    test_run_number = 58848
    test_log_name = 'loadframe.stress'

    # Get workflow
    wk_flow = my_data.get()
    assert(isinstance(wk_flow, vdapi.VDriveAPI))

    status, ret_obj = wk_flow.slice_data(run_number=test_run_number,
                                         sample_log_name=test_log_name)
    assert_true(status)
    if status is False:
        return

    # Check number of output workspace
    split_ws_name_list = ret_obj
    num_split_ws = len(split_ws_name_list)
    assert_equals(num_split_ws, 3)

    # Use simple math to do the check
    if False:
        num_raw_events = wk_flow.get_number_events(run_number=test_run_number)
        num_split_ws_events = 0
        for split_ws_name in vec_split_ws:
            partial_num_events = wk_flow.get_number_events(split_ws_name)
            num_split_ws_events += partial_num_events
        assert_equals(num_raw_events, num_split_ws_events)

    return


@step(u'Then I set up rules to slice this run by time')
def generate_data_slicer_by_time(step):
    """
    Set up rules and create data slicer/event splitters by sample log value
    :param step:
    :return:
    """
    test_run_number = 58848

    # Get workflow
    wk_flow = my_data.get()
    assert(isinstance(wk_flow, vdapi.VDriveAPI))

    # Set up rule
    status, ret_obj = wk_flow.gen_data_slicer_by_time(run_number=test_run_number,
                                                      start_time=1.0,
                                                      end_time=200.1,
                                                      time_step=10.)

    return


@step(u'I have data sliced by time-splitters and check result')
def slice_data_by_time(step):
    """ Slice data by current splitters
    :param step:
    :return:
    """
    test_run_number = 58848
    test_log_name = 'loadframe.stress'

    # Get workflow
    wk_flow = my_data.get()
    assert(isinstance(wk_flow, vdapi.VDriveAPI))

    status, ret_obj = wk_flow.slice_data(run_number=test_run_number,
                                         by_time=True)

    return


if True:
    setup_ipts(1)
    filter_runs(2)
    set_ipts_runs(3)
    input_sample_log_name(4)
    generate_data_slicer(5)
    slice_data(6)
    generate_data_slicer_by_time(7)
    slice_data_by_time(8)

