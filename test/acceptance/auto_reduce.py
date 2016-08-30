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
ipts_number = 16002


@step(u'I get one run belonged to an IPTS number')
def init_workflow(step):
    """ Do nothing at all.  It is a given situation and it won't be called.
    """
    pass

@step(u'I create a reduction project')
def initialize_project(step):
    """
    Initialize the workflow instance and set up a reduction project
    :param step:
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


@step(u'I set the IPTS number and get runs from its archive')
def setup_ipts(step):
    """ Set up IPTS, run number and etc for reduction
    """
    # Get workflow
    wk_flow = my_data.get()

    # Set up IPTS
    assert ipts_number is not None
    wk_flow.set_ipts(ipts_number)

    # Get runs
    status, run_tup_list = wk_flow.get_ipts_info(ipts_number)
    assert_equals(status, True)

    my_data.set_ipts_runs(ipts_number, run_tup_list)

    return


@step(u'I add just a few runs')
def filter_runs_by_run(step):
    """ Filter runs by date
    """
    this_ipts_number, run_tup_list = my_data.get_ipts_runs()

    first_run = 80230
    last_run = 80240
    status, filter_run_tup_list = vdapi.filter_runs_by_run(run_tup_list, first_run, last_run)
    assert_equals(status, True)
    assert_equals(len(filter_run_tup_list), 10)

    my_data.set_ipts_runs(ipts_number, filter_run_tup_list)

    return


@step(u'I check IPTS and run numbers from the workflow instance')
def set_ipts_runs(step):
    """
    """
    wk_flow = my_data.get()
    this_ipts_number, run_tup_list = my_data.get_ipts_runs()

    status, error_message = wk_flow.clear_runs()
    assert_equals(status, True)

    status, error_message = wk_flow.add_runs_to_project(run_tup_list, this_ipts_number)
    assert_equals(status, True)
    assert_equals(10, wk_flow.get_number_runs())

    return


@step(u'I add a run number to the VDrive project for reduction')
def add_run_to_reduce(step):
    """ Add a run to reduce
    :param step:
    :return:
    """
    workflow = my_data.get()

    workflow.set_runs_to_reduce(run_numbers=[80231])

    return


@step(u'I reduce the specified Vulcan run')
def reduce_single_set_data(step):
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
    reduction_list = [(80231, True)]
    workflow.set_reduction_flag(file_flag_list=reduction_list, clear_flags=True)

    status, ret_obj = workflow.reduce_data_set(norm_by_vanadium=False)
    print\
        '[Message] ', str(ret_obj)
    print
    assert_true(status, str(ret_obj))

    return


@step(u'I export the reduced data to GSAS file')
def export_to_gsas(step=9):
    """ Test retrieve reduced data
    :param step:
    :return:
    """
    # Get workflow
    work_flow = my_data.get()

    output_file_name = '/tmp/acceptance_test.gda'

    # Clear the file if it exists.
    if os.path.exists(output_file_name):
        os.remove(output_file_name)

    status = work_flow.export_gsas_file(run_number=80231)
    assert_true(status)

    # Check existence of the
    assert_true(os.path.exists(output_file_name))

    return

# TODO/NOW/1st: Think of some crazy things to process the reduced data such as normalize by current, change unit, and etc.


if __name__ == "__main__":

    if False:
        init_workflow(0)
        initialize_project(1)
        setup_ipts(2)
        filter_runs_by_run(3)
        set_ipts_runs(4)
        add_run_to_reduce(7)
        reduce_single_set_data(8)
        export_to_gsas(9)

