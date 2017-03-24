################################################################################
# Manage the reduced VULCAN runs
################################################################################
import os
import reduce_VULCAN
import mantid_helper
import chop_utility

EVENT_WORKSPACE_ID = "EventWorkspace"


class DataReductionTracker(object):
    """ Record tracker of data reduction for an individual run.
    """
    FilterBadPulse = 1
    AlignAndFocus = 2
    NormaliseByCurrent = 3
    CalibratedByVanadium = 4

    def __init__(self, run_number, ipts_number):
        """
        Purpose:
            Initialize an object of DataReductionTracer
        Requirements:
            1. run number is integer
            2. file path is string
            3. vanadium calibration is a string for calibration file. it could be none
        :return:
        """
        # Check requirements
        assert isinstance(run_number, int), 'Run number {0} must be an integer but not {1}.' \
                                            ''.format(run_number, type(run_number))
        assert isinstance(ipts_number, int), 'IPTS number {0} must be an integer but not {1}.' \
                                             ''.format(ipts_number, type(ipts_number))

        # set up
        self._runNumber = run_number
        # FIXME - it is not clear whether it is better to use vanadium file name or vanadium run number
        self._vanadiumCalibrationRunNumber = None
        self._iptsNumber = ipts_number

        # Workspaces' names
        # event workspaces
        self._eventWorkspace = None
        self._vdriveWorkspace = None
        self._tofWorkspace = None
        self._dspaceWorkspace = None

        # status flag
        self._isReduced = False

        # initialize states of reduction beyond
        self._badPulseRemoved = False
        self._normalisedByCurrent = False
        self._correctedByVanadium = False

        # reduced file list
        self._reducedFiles = None

        # variables about chopped workspaces
        self._slicerKey = None   # None stands for the reduction is without chopping
        self._choppedWorkspaceNameList = None

        return

    def set_reduced_files(self, file_name_list, append):
        """
        add reduced file
        :param file_name_list:
        :return:
        """
        assert isinstance(file_name_list, list), 'Input file names must be in a list but not {0}.' \
                                                 ''.format(type(file_name_list))

        if not append or self._reducedFiles is None:
            self._reducedFiles = file_name_list[:]
        else:
            self._reducedFiles.extend(file_name_list[:])

        return

    @property
    def dpsace_worksapce(self):
        """
        Mantid binned DSpaceing workspace
        :return:
        """
        return self._dspaceWorkspace

    @property
    def event_workspace_name(self):
        """
        Get the name of the event workspace
        :return:
        """
        return self._eventWorkspace

    @event_workspace_name.setter
    def event_workspace_name(self, value):
        """
        Set the name of the event workspace.  This operation might be called
        before the workspace is created.
        Requirements:
            1. Input is a string
        :param value:
        :return:
        """
        # Check
        assert isinstance(value, str), 'Input workspace name must be string but not %s.' % str(type(value))
        # Set
        self._eventWorkspace = value

    def get_information(self):
        """
        construct information about the chopped workspace
        :return:
        """
        info_dict = dict()
        info_dict['run'] = self._runNumber
        info_dict['reduced'] = self._isReduced
        if self._slicerKey is None:
            # regular reduced data
            info_dict['slicer_key'] = None
        else:
            # chopped run
            info_dict['slicer_key'] = self._slicerKey
            info_dict['workspaces'] = self._choppedWorkspaceNameList[:]
            if self._reducedFiles is not None:
                info_dict['files'] = self._reducedFiles[:]
            else:
                info_dict['files'] = None

        return info_dict

    def get_reduced_gsas(self):
        """

        :return:
        """
        gsas_file = None

        for file_name in self._reducedFiles:
            main_file_name, file_ext = os.path.splitext(file_name)
            if file_ext.lower() in ['.gda', '.gsas', '.gsa']:
                gsas_file = file_name
                break

        if gsas_file is None:
            raise RuntimeError('Unable to locate reduced GSAS file of run {0}.  '
                               'Files found are {1}'.format(self._runNumber, self._reducedFiles))

        return gsas_file

    @property
    def ipts_number(self):
        """
        get the IPTS number set to this run number
        :return:
        """
        return self._iptsNumber

    @property
    def is_chopped_run(self):
        """
        check whether the reduction is about a chopped run
        :return:
        """
        return self._slicerKey is not None

    @property
    def is_corrected_by_vanadium(self):
        """

        :return:
        """
        return self._correctedByVanadium

    @is_corrected_by_vanadium.setter
    def is_corrected_by_vanadium(self, state):
        """

        :param state:
        :return:
        """
        assert isinstance(state, bool), 'Flag/state must be a boolean'
        self._correctedByVanadium = state

    @property
    def is_normalized_by_current(self):
        """

        :return:
        """
        return self._normalisedByCurrent

    @is_normalized_by_current.setter
    def is_normalized_by_current(self, state):
        """

        :param state:
        :return:
        """
        assert isinstance(state, bool)

        self._normalisedByCurrent = state

    @property
    def is_reduced(self):
        """ Check whether the event data that has been reduced
        :return:
        """
        return self._isReduced

    @is_reduced.setter
    def is_reduced(self, value):
        """
        Purpose: set the status that the event data has been reduced
        Requirements: value is boolean
        Guarantees:
        :param value:
        :return:
        """
        assert isinstance(value, bool), 'Input for is_reduced must be a boolean but not %s.' % str(type(value))
        self._isReduced = value

    @property
    def is_raw(self):
        """
        Show the status whether the workspace has never been processed
        :return:
        """
        return not self._isReduced

    @property
    def run_number(self):
        """ Read only to return the run number that this tracker
        :return:
        """
        return self._runNumber

    @property
    def vdrive_workspace(self):
        """
        VDrive-binned workspace
        :return:
        """
        return self._vdriveWorkspace

    @property
    def tof_workspace(self):
        """
        Mantid binned TOF workspace
        :return:
        """
        return self._tofWorkspace

    def set_chopped_workspaces(self, workspace_name_list, append):
        """
        set the chopped workspaces' names
        :param workspace_name_list:
        :param append: append chopped workspaces
        :return:
        """
        # check inputs
        assert isinstance(workspace_name_list, list), 'Input list of workspaces names {1} must be list but not a {1}.' \
                                                      ''.format(workspace_name_list, type(workspace_name_list))

        if self._choppedWorkspaceNameList is None or not append:
            self._choppedWorkspaceNameList = workspace_name_list[:]
        else:
            self._choppedWorkspaceNameList.extend(workspace_name_list)

        return

    def set_reduced_workspaces(self, vdrive_bin_ws, tof_ws, dspace_ws):
        """

        :param vdrive_bin_ws:
        :param tof_ws:
        :param dspace_ws:
        :return:
        """
        # check workspaces existing
        assert mantid_helper.workspace_does_exist(vdrive_bin_ws), 'VDrive-binned workspace {0} does not exist ' \
                                                                  'in ADS'.format(vdrive_bin_ws)
        assert mantid_helper.workspace_does_exist(tof_ws), 'Mantid-binned TOF workspace {0} does not exist in ADS.' \
                                                           ''.format(tof_ws)
        assert mantid_helper.workspace_does_exist(dspace_ws), 'Mantid-binned D-space workspace {0} does not exist ' \
                                                              'in ADS.'.format(dspace_ws)
        dspace_ws_unit = mantid_helper.get_workspace_unit(dspace_ws)
        assert dspace_ws_unit == 'dSpacing',\
            'The unit of DSpace workspace {0} should be dSpacing but not {1}.'.format(str(dspace_ws), dspace_ws_unit)

        self._vdriveWorkspace = vdrive_bin_ws
        self._tofWorkspace = tof_ws
        self._dspaceWorkspace = dspace_ws

        self._isReduced = True

        return

    def set_slicer_key(self, slicer_key):
        """
        set slicer key to the
        :param slicer_key:
        :return:
        """
        self._slicerKey = slicer_key

        return

    @property
    def vanadium_calibration(self):
        """
        Return vanadium calibration run number
        :return:
        """
        return self._vanadiumCalibrationRunNumber

    @vanadium_calibration.setter
    def vanadium_calibration(self, value):
        """
        Set vanadium calibration run number
        Purpose:
        Requirements:
            value is integer
        Guarantees:
            vanadium run number is set
        :param value:
        :return:
        """
        assert isinstance(value, int), 'Input value should be integer for run number'
        self._vanadiumCalibrationRunNumber = value

        return


class ReductionManager(object):
    """ Class ReductionManager takes the control of reducing SNS/VULCAN's event data
    to diffraction pattern for Rietveld analysis.

    * Business model and technical model
      - Run number as integers or data file name are used to communicate with client;
      - Workspace names are used for internal communications.

    Its main data structure contains
    1. a dictionary of reduction controller
    2. a dictionary of loaded vanadium

    ??? It is able to reduce the data file in the format of data file,
    run number and etc. 

    ??? It supports event chopping.
    """
    SUPPORTED_INSTRUMENT = ['VULCAN']

    def __init__(self, instrument):
        """
        Purpose:

        Requirements:
            1. instrument is a valid instrument's name
        Guarantees:
        :param instrument:
        :return:
        """
        # Check requirements
        assert isinstance(instrument, str), 'Input instrument must be of type str'
        instrument = instrument.upper()
        assert instrument in ReductionManager.SUPPORTED_INSTRUMENT, \
            'Instrument %s is not in the supported instruments (%s).' % (instrument,
                                                                         ReductionManager.SUPPORTED_INSTRUMENT)

        # Set up including default
        self._myInstrument = instrument

        # reduction tracker: key = run number (integer), value = DataReductionTracker
        self._reductionTrackDict = dict()

        return

    def chop_data(self, ipts_number, run_number, data_file, chop_manager, slice_key, output_dir, tof_correction=False):
        """
        chop data from a source event file and then save the result to Nexus files.
        There is no focusing type of reduction is evolved.
        :param ipts_number:
        :param run_number
        :param data_file:
        :param chop_manager:
        :param slice_key:
        :param output_dir:
        :param tof_correction: default to False.  applied if the log is fast
        :return:
        """
        # check inputs
        assert isinstance(chop_manager, chop_utility.DataChopper), \
            'Input chopper manager must be an instance of DataChopper but not {0}.' \
            ''.format(chop_manager.__class__.__name__)
        assert isinstance(run_number, int), 'Run number must be an integer but not of type {0}.' \
                                            ''.format(type(run_number))
        assert isinstance(ipts_number, int), 'IPTS number {0} must be an integer but not a {1}.' \
                                             ''.format(ipts_number, type(ipts_number))

        # get splitters workspace
        #

        # split event data
        status, ret_obj = chop_manager.chop_data(raw_file_name=data_file,
                                                 splice_key=slice_key,
                                                 output_directory=output_dir)

        if status:
            chopped_ws_name_list = ret_obj
        else:
            error_msg = ret_obj
            return False, error_msg

        self.init_tracker(ipts_number=ipts_number, run_number=run_number, slicer_key=slice_key)
        if ret_obj is not None:
            self._reductionTrackDict[run_number, slice_key].set_chopped_workspaces(chopped_ws_name_list)
        # TODO/ISSUE/33 - Consider to record saved NeXus file names

        return True, None

    def get_event_workspace_name(self, run_number):
        """
        Get or generate the name of a raw event workspace
        Requirements: run number must be a positive integer
        :param run_number:
        :return:
        """
        assert isinstance(run_number, int), 'Input run number must be an integer but not {0}.'.format(type(run_number))
        assert run_number > 0, 'Given run number {0} must be a positive number.'.format(run_number)

        event_ws_name = '%s_%d_events' % (self._myInstrument, run_number)

        return event_ws_name

    def get_reduced_data(self, run_number, unit):
        """ Get data (x, y and e) of a reduced run in the specified unit
        Purpose: Get reduced data including all spectra
        Requirements: run number is a valid integer; unit is a string for supported unit
        Guarantees: all data of the reduced run will be returned
        :param run_number:
        :param unit: target unit for the output X vector.  If unit is None, then no request
        :return: dictionary: key = spectrum number, value = 3-tuple (vec_x, vec_y, vec_e)
        """
        # check
        assert isinstance(run_number, int), 'Input run number must be an integer.'
        assert unit is None or isinstance(unit, str), 'Output data unit must be either None (default) or a string.'

        # get reduced workspace name
        reduced_ws_name = self.get_reduced_workspace(run_number, is_vdrive_bin=True, unit='TOF')

        # get data
        data_set_dict, unit = mantid_helper.get_data_from_workspace(reduced_ws_name, target_unit=unit,
                                                                    point_data=True, start_bank_id=True)
        assert isinstance(data_set_dict, dict), 'Returned value from get_data_from_workspace must be a dictionary,' \
                                                'but not %s.' % str(type(data_set_dict))

        return data_set_dict

    def get_reduced_file(self, run_number, file_type):
        """

        :param run_number:
        :param file_type:
        :return:
        """
        # check inputs
        assert isinstance(file_type, str) and file_type in ['gda', 'gsas', 'gss'],\
            'File type {0} is not supported.'.format(file_type)

        if file_type in ['gda', 'gsas', 'gsa']:
            file_name = self._reductionTrackDict[run_number].get_reduced_gsas()
        else:
            raise RuntimeError('Not Implemented yet!')

        return file_name

    def get_reduced_run(self, ipts_number, run_number):
        """
        get the workspace key to a reduced run
        :param ipts_number:
        :param run_number:
        :return:
        """
        if (ipts_number, run_number) in self._reductionTrackDict:
            return ipts_number, run_number

        return None

    def get_reduced_runs(self, with_ipts=False):
        """
        Get the runs that have been reduced. It is just for information
        :return:  a list of run numbers
        """
        return_list = list()
        for run_number in self._reductionTrackDict.keys():
            tracker = self._reductionTrackDict[run_number]
            if tracker.is_reduced is True:
                if with_ipts:
                    new_item = run_number, tracker.ipts_number
                else:
                    new_item = run_number

                return_list.append(new_item)
            # END-IF
        # END-FOR

        return return_list

    def get_reduced_workspace(self, run_number, is_vdrive_bin=True, unit='TOF'):
        """ Get the reduced matrix workspace
        Requirements:
            1. Specified run is correctly reduced;
        Guarantees:
            2. Return reduced workspace's name
        Arguments:
         - unit :: target unit; If None, then no need to convert unit
        :exception: Assertion Error if run number does not exist in self._reductionTrackDict
        :exception: RuntimeError if unit is not supported
        :param run_number:
        :param is_vdrive_bin:
        :param unit:
        :return: Workspace (success) or 2-tuple (False and error message)
        """
        # Check requirements
        assert isinstance(run_number, int), 'Run number must be integer but not %s.' % str(type(run_number))
        # get tracker
        assert run_number in self._reductionTrackDict, 'Run number {0} is not reduced.'.format(run_number)
        tracker = self._reductionTrackDict[run_number]
        assert isinstance(tracker, DataReductionTracker), 'Stored tracker must be an instance of DataReductioTracker.'

        if is_vdrive_bin and unit != 'TOF':
            raise RuntimeError('It is possible to get a VDrive-binned workspace in unit {0} other than TOF.'
                               ''.format(unit))
        elif unit != 'TOF' and unit.lower() != 'dspace':
            raise RuntimeError('Unit {0} is not supported.'.format(unit))

        if is_vdrive_bin:
            return_ws_name = tracker.vdrive_workspace
        elif unit == 'TOF':
            return_ws_name = tracker.tof_workspace
        else:
            return_ws_name = tracker.dpsace_worksapce

        return return_ws_name

    def has_run(self, run_number):
        """
        check whether a certain run number is reduced and stored
        :param run_number:
        :return:
        """
        return run_number in self._reductionTrackDict

    def init_tracker(self, ipts_number, run_number, slicer_key=None):
        """ Initialize tracker
        :param run_number:
        :param slicer_key: if not specified, then the reduction is without chopping
        :return:
        """
        # Check requirements
        assert isinstance(ipts_number, int) or ipts_number is None, 'IPTS number {0}  must be an integer or None but ' \
                                                                    'not a {1}.'.format(ipts_number, type(ipts_number))
        assert isinstance(run_number, int), 'Run number %s must be integer but not %s' % (str(run_number),
                                                                                          str(type(run_number)))

        # Initialize a new tracker
        if slicer_key is None:
            tracker_key = run_number
        else:
            tracker_key = run_number, slicer_key

        if ipts_number is None:
            raise NotImplementedError('Figure out how to track a reduction without a good IPTS number!')

        if tracker_key not in self._reductionTrackDict:
            new_tracker = DataReductionTracker(run_number, ipts_number)
            new_tracker.set_slicer_key(slicer_key)
            self._reductionTrackDict[tracker_key] = new_tracker
        else:
            # existing tracker: double check
            assert isinstance(self._reductionTrackDict[run_number], DataReductionTracker),\
                'It is not DataReductionTracker but a {0}.'.format(type(self._reductionTrackDict[run_number]))

        return

    def get_tracker(self, run_number, slicer_key):
        """
        get a reduction tracker
        :param run_number:
        :param slicer_key:
        :return:
        """
        # construct a tracker key
        tracker_key = run_number, slicer_key
        if tracker_key in self._reductionTrackDict:
            tracker = self._reductionTrackDict[tracker_key]
        else:
            raise RuntimeError('Unable to locate tracker with run: {0} slicer: {1}.  Existing keys are {2}'
                               ''.format(run_number, slicer_key, self._reductionTrackDict.keys()))

        return tracker

    def reduce_chopped_data(self, ipts_number, run_number, src_file_name, chop_manager, slicer_key, output_dir):
        """
        reduce chopped data to GSAS file
        :param ipts_number:
        :param run_number:
        :param src_file_name: original event data from which the events are split
        :param chop_manager: a ChopperManager instance which manages the split workspace
        :param slicer_key:
        :param output_dir:
        :return:
        """
        import reduce_adv_chop

        # check inputs
        assert isinstance(ipts_number, int), 'IPTS number {0} must be an integer ' \
                                             'but not {1}.'.format(ipts_number, type(ipts_number))
        assert isinstance(run_number, int), 'Input run number {0} must be an integer ' \
                                            'but not {1}.'.format(run_number, type(run_number))

        # retrieve split workspace and split information workspace from chopper manager
        split_ws_name, info_ws_name = chop_manager.get_split_workspace(slicer_key)

        # initialize a ReductionSetup instance
        reduce_setup = reduce_VULCAN.ReductionSetup()

        reduce_setup.set_ipts_number(ipts_number)
        reduce_setup.set_run_number(run_number)
        reduce_setup.set_event_file(src_file_name)

        reduce_setup.set_output_dir(output_dir)
        reduce_setup.set_gsas_dir(output_dir, main_gsas=True)
        reduce_setup.is_full_reduction = False
        reduce_setup.set_default_calibration_files()

        # add splitter workspace and splitter information workspace
        reduce_setup.set_splitters(split_ws_name, info_ws_name)

        #  reducer = reduce_VULCAN.ReduceVulcanData(reduce_setup)
        reducer = reduce_adv_chop.AdvancedChopReduce(reduce_setup)

        reducer.execute_chop_reduction(clear_workspaces=False)

        # get the reduced file names and workspaces and add to reduction tracker dictionary
        self.init_tracker(ipts_number, run_number, slicer_key)

        # TEST/ISSUE/33/
        reduced, workspace_name_list = reducer.get_reduced_workspaces(chopped=True)
        self.set_chopped_reduced_workspaces(run_number, slicer_key, workspace_name_list, append=True)
        self.set_chopped_reduced_files(run_number, slicer_key, reducer.get_reduced_files(), append=True)

        return True, None

    def reduce_run(self, ipts_number, run_number, event_file, output_directory, vanadium=False,
                   vanadium_tuple=None, gsas=True, standard_sample_tuple=None, binning_parameters=None):
        """
        Reduce run with selected options
        Purpose:
        Requirements:
        Guarantees:
        :param ipts_number:
        :param run_number:
        :param event_file:
        :param output_directory:
        :param vanadium:
        :param vanadium_tuple:
        :param gsas:
        :param standard_sample_tuple:
        :param binning_parameters:
        :return:
        """
        # set up reduction options
        reduction_setup = reduce_VULCAN.ReductionSetup()
        reduction_setup.set_default_calibration_files()

        # run number, ipts and etc
        reduction_setup.set_run_number(run_number)
        reduction_setup.set_event_file(event_file)
        reduction_setup.set_ipts_number(ipts_number)
        if binning_parameters is not None:
            reduction_setup.set_mantid_binning(binning_parameters)

        # vanadium
        reduction_setup.normalized_by_vanadium = vanadium
        if vanadium:
            assert isinstance(vanadium_tuple, tuple) and len(vanadium_tuple) == 3,\
                'Input vanadium-tuple must be a tuple with length 3.'
            van_run, van_gda, vanadium_tag = vanadium_tuple
            reduction_setup.set_vanadium(van_run, van_gda, vanadium_tag)

        # outputs
        reduction_setup.set_output_dir(output_directory)
        if gsas:
            reduction_setup.set_gsas_dir(output_directory, True)

        # process on standards
        if standard_sample_tuple:
            assert isinstance(standard_sample_tuple, tuple) and len(standard_sample_tuple) == 3,\
                'Input standard sample-tuple must be a tuple with length 3 but not a {0}.'.format(standard_sample_tuple)
            standard_sample, standard_dir, standard_record_file = standard_sample_tuple
            reduction_setup.is_standard = True
            reduction_setup.set_standard_sample(standard_sample, standard_dir, standard_record_file)
        # END-IF (standard sample tuple)

        # reduce
        reducer = reduce_VULCAN.ReduceVulcanData(reduction_setup)
        reduce_good, message = reducer.execute_vulcan_reduction()

        # record reduction tracker
        if reduce_good:
            self.init_tracker(ipts_number, run_number)

            if vanadium:
                self._reductionTrackDict[run_number].is_corrected_by_vanadium = True

            # set reduced files
            self._reductionTrackDict[run_number].set_reduced_files(reducer.get_reduced_files(), append=False)
            # set workspaces
            status, ret_obj = reducer.get_reduced_workspaces(chopped=False)
            if status:
                # it may not have the workspace because
                vdrive_ws, tof_ws, d_ws = ret_obj
                self.set_reduced_workspaces(run_number, vdrive_ws, tof_ws, d_ws)

        # END-IF

        return reduce_good, message

    def set_chopped_reduced_workspaces(self, run_number, slicer_key, workspace_name_list, append=False, compress=False):
        """
        set the chopped and reduced workspaces to reduction manager
        :param run_number:
        :param slicer_key:
        :param workspace_name_list:
        :param append:
        :param compress: if compress, then merge all the 2-bank workspace together   NOTE: using ConjoinWorkspaces???
        :return:
        """
        # get tracker
        tracker = self.get_tracker(run_number, slicer_key)

        # add files
        assert isinstance(tracker, DataReductionTracker), 'Must be a DataReductionTracker'
        tracker.set_chopped_workspaces(workspace_name_list, append=True)

        if compress:
            tracker.make_compressed_reduced_workspace(workspace_name_list)

        return

    def set_chopped_reduced_files(self, run_number, slicer_key, gsas_file_list, append):
        """
        set the reduced file
        :param run_number:
        :param slicer_key:
        :param gsas_file_list:
        :param append:
        :return:
        """
        # get tracker
        tracker = self.get_tracker(run_number, slicer_key)
        assert isinstance(tracker, DataReductionTracker), 'Must be a DataReductionTracker'

        # add files
        tracker.set_reduced_files(gsas_file_list, append)

        return

    def set_reduced_workspaces(self, run_number, vdrive_bin_ws, tof_ws, dspace_ws):
        """
        set a run's reduced workspaces
        :param run_number: int
        :param vdrive_bin_ws: str
        :param tof_ws: str
        :param dspace_ws: str
        :return:
        """
        # check
        assert isinstance(run_number, int), 'Input run number {0} must be a integer but not {1}.' \
                                            ''.format(run_number, type(run_number))
        assert isinstance(vdrive_bin_ws, str) and isinstance(tof_ws, str) and isinstance(dspace_ws, str),\
            'VDRIVE-binning workspace name {0}, TOF workspace name {1} and Dspacing workspace {2} must be a string.' \
            ''.format(vdrive_bin_ws, tof_ws, dspace_ws)

        self._reductionTrackDict[run_number].set_reduced_workspaces(vdrive_bin_ws, tof_ws, dspace_ws)

        return

