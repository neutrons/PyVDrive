import sys
sys.path.append('/SNS/users/wzz/Mantid_Project/builds/build-vulcan/bin')

import numpy
import mantid.simpleapi as mantidsimple
import mantid
from mantid.api import AlgorithmManager
from mantid.api import AnalysisDataService as ADS
import mantid_helper
import peak_util
import archivemanager
from PyQt4 import QtCore

# TODO/ISSUE/NEXT - Find out how to use log files
# .. LOG_NAME = 'livereduce'  # constant for logging
# .. LOG_FILE = '/var/log/SNS_applications/livereduce.log'
# .. logger = logging.getLogger(__name__)
# .. logger.setLevel(logging.INFO)


class LiveDataDriver(QtCore.QThread):
    """
    Driver/manager for live data monitoring and reduction
    """
    COUNTER_WORKSPACE_NAME = '_VULCAN_LIVE_COUNTER'
    # TODO/FIXME/NOW - Make this script more robust and informative
    # LIVE_PROCESS_SCRIPTS = '/home/wzz/Mantid_Project/builds/vulcan_live_data_test.py'  # local test only
    # LIVE_PROCESS_SCRIPTS = '/SNS/VULCAN/shared/livereduce/vulcan_live_data_beta.py'
    LIVE_PROCESS_SCRIPTS = '/SNS/VULCAN/shared/livereduce/vulcan_live_data_v0_9.py'

    def __init__(self):
        """
        initialization
        """
        super(LiveDataDriver, self).__init__()

        # archive manager
        self._archiveManager = archivemanager.DataArchiveManager('VULCAN')

        # clear the existing workspace with same name
        if mantid_helper.workspace_does_exist(LiveDataDriver.COUNTER_WORKSPACE_NAME):
            mantid_helper.delete_workspace(LiveDataDriver.COUNTER_WORKSPACE_NAME)

        # create workspace: workspace index 1 will be used to record number of events
        mantidsimple.CreateWorkspace(OutputWorkspace=LiveDataDriver.COUNTER_WORKSPACE_NAME,
                                     DataX=[0, 0], DataY=[0, 0], NSpec=2)

        # get the live reduction script
        self._live_reduction_script = LiveDataDriver.LIVE_PROCESS_SCRIPTS

        self._thread_continue = True

        # more containers
        self._peakIntensityDict = dict()  # key: workspace name. value: 2-tuple (avg time (epoch/second, peak intensity)

        self._vanadiumWorkspaceDict = dict()  # key: bank ID.  value: workspace name

        return

    def calculate_live_peak_parameters(self, ws_name, bank_id, norm_by_van, d_min, d_max):
        """
        blabla
        :param ws_name:
        :param bank_id
        :param norm_by_van:
        :param d_min:
        :param d_max:
        :return: 3-tuple as (peak integrated intensity, average dSpacing value, variance)
        """
        # check inputs
        assert isinstance(ws_name, str), 'Input workspace name {0} must be a string but not a {1}' \
                                         ''.format(ws_name, type(ws_name))

        # TODO/NOW - check input babla ASAP

        # check bank ID
        if bank_id < 1 or bank_id > 3:
            raise RuntimeError('Bank ID {0} is out of range.'.format(bank_id))
        else:
            ws_index = bank_id - 1

        # get workspace
        workspace = mantid_helper.retrieve_workspace(ws_name, True)

        # calculate x min and x max indexes
        vec_d = workspace.readX(ws_index)
        min_x_index = max(0, numpy.searchsorted(vec_d, d_min) - 1)
        max_x_index = min(len(vec_d), numpy.searchsorted(vec_d, d_max) + 1)

        # get Y
        vec_y = workspace.readY(ws_index)
        if norm_by_van and bank_id in self._vanadiumWorkspaceDict:
            # normalize vanadium if the flag is on AND vanadium is loaded
            vec_van = self.get_vanadium(bank_id)
            vec_y = vec_y / vec_van

        # estimate background
        bkgd_a, bkgd_b = peak_util.estimate_background(vec_d, vec_y, min_x_index, max_x_index)

        # calculate peak intensity parameters
        try:
            peak_integral, average_d, variance = peak_util.calculate_peak_variance(vec_d, vec_y, min_x_index,
                                                                                   max_x_index, bkgd_a, bkgd_b)
        except ValueError:
            peak_integral = -1.E-20
            average_d = 0.5 * (d_max + d_min)
            variance = 0

        return peak_integral, average_d, variance

    @staticmethod
    def convert_time_stamps(date_time_vec, relative):
        """convert a vector of DateAndTime instance to a vector of double as relative
        time to a specified time in DateAndTime
        :param date_time_vec:
        :param relative: start time
        :return: a vector of time stamps in double/float in unit of seconds
        """
        # check inputs
        assert isinstance(date_time_vec, numpy.ndarray) or \
               isinstance(date_time_vec, mantid.kernel._kernel.std_vector_dateandtime),\
            'Input time vector must be a numpy.array but not a {0}.'.format(type(date_time_vec))
        assert relative is None or relative.__class__.__name__.count('DateAndTime') > 0, \
            'Relative time {0} must be None or a DateAndTime instance but not a {1}.' \
            ''.format(relative, type(relative))

        # create an array
        shape = len(date_time_vec)
        time_vec = numpy.ndarray(shape=(shape,), dtype='float')

        if relative is None:
            start_time = 0
        else:
            start_time = relative.totalNanoseconds()

        # convert
        for i in range(shape):
            time_i = (date_time_vec[i].totalNanoseconds() - start_time) * 1.E-9
            time_vec[i] = time_i

        return time_vec

    @staticmethod
    def convert_unit(src_ws, target_unit, new_ws_name):
        """Convert the unit of a workspace
        :param src_ws:
        :param target_unit:
        :param new_ws_name:
        :return:
        """
        # check
        assert isinstance(target_unit, str), 'Target unit {0} must be string but not a {1}' \
                                             ''.format(target_unit, type(target_unit))
        assert isinstance(new_ws_name, str), 'New workspace name {0} must be string but not a {1}.' \
                                             ''.format(new_ws_name, type(new_ws_name))

        # convert workspace to workspace
        if isinstance(src_ws, str):
            if ADS.doesExist(src_ws) is False:
                raise RuntimeError('Source workspace with name {0} for unit conversion does not exist.'
                                   ''.format(src_ws))
            src_ws = ADS.retrieve(src_ws)
        else:
            assert src_ws is not None, 'Source workspace of convert unit cannot be None.'

        # check units
        src_unit = src_ws.getAxis(0).getUnit().unitID()
        if src_unit == target_unit:
            # same unit. do nothing.  copy reference and return
            new_ws = src_ws
            is_new_ws = False
        else:
            # covert unit by calling Mantid
            mantidsimple.ConvertUnits(InputWorkspace=src_ws, Target=target_unit, OutputWorkspace=new_ws_name)
            new_ws = ADS.retrieve(new_ws_name)
            is_new_ws = True
        # END-IF

        return new_ws, is_new_ws

    @staticmethod
    def delete_workspace(workspace_name, no_throw=False):
        """
        Delete a workspace from Mantid's AnalysisDataService
        Args:
            workspace_name: name of a workspace as a string instance
            no_throw: if True, then it won't throw any exception if the workspace does not exist in AnalysisDataService

        Returns: None

        """
        # check
        assert isinstance(workspace_name, str), \
            'Input workspace name must be a string, but not %s.' % str(type(workspace_name))

        # check whether the workspace exists
        does_exit = ADS.doesExist(workspace_name)
        if does_exit:
            # delete
            mantid_helper.delete_workspace(workspace=workspace_name)
        elif not no_throw:
            raise RuntimeError('Workspace %s does not exist.' % workspace_name)

        return

    @staticmethod
    def get_live_counter():
        """
        check
        :return:
        """
        counter_ws = mantid_helper.retrieve_workspace(LiveDataDriver.COUNTER_WORKSPACE_NAME)
        curr_index = counter_ws.readX(0)[0]

        return curr_index

    @staticmethod
    def get_live_events():
        """
        check
        :return:
        """
        counter_ws = mantid_helper.retrieve_workspace(LiveDataDriver.COUNTER_WORKSPACE_NAME)
        live_events = counter_ws.readX(1)[0]

        return live_events

    @staticmethod
    def get_workspaces():
        """get the workspace from Mantid ADS
        :except: RuntimeError if ADS crashes
        :return:
        """
        try:
            ws_names = ADS.getObjectNames()
        except RuntimeError as run_err:
            raise RuntimeError('Unable to get workspaces\' names from ADS due to \n{0}'.format(run_err))
        
        return ws_names

    def get_peaks_parameters(self, param_type, bank_id_list, time0):
        """ get the peaks' positions (calculated) along with time
        :param param_type:
        :param bank_id_list: bank IDs
        :param time0: time zero for time stamps
        :return:
        """
        # check whether inputs are valid
        assert isinstance(bank_id_list, list), 'Bank ID list {0} must be an integer but not a {1}.' \
                                               ''.format(bank_id_list, type(bank_id_list))
        assert isinstance(param_type, str), 'Peak parameter type {0} must be a string but not a {1}.' \
                                            ''.format(param_type, type(param_type))

        # time 0
        try:
            time0_ns = time0.totalNanoseconds()
        except AttributeError as att_err:
            raise RuntimeError('Time Zero must be a DateAndTime instance: {0}'
                               ''.format(att_err))

        # get peak type
        if param_type == 'center':
            type_index = 2
        elif param_type == 'intensity':
            type_index = 1
        else:
            raise RuntimeError('Peak parameter type {0} is not recognized. Supported are "center" and "intensity"'
                               ''.format(param_type))

        # parse data
        param_table_list = list()
        for tup_value in self._peakIntensityDict.values():
            # each time stamp
            # get values of all banks
            time_i, intensities, positions = tup_value
            # get time
            time_i_rel = (time_i.totalNanoseconds() - time0_ns) * 1.E-9

            list_i = [time_i_rel]
            # peak parameter value
            for bank_id in bank_id_list:
                ws_index = bank_id - 1
                if type_index == 1:
                    value_i = intensities[ws_index]
                elif type_index == 2:
                    value_i = positions[ws_index]
                else:
                    raise NotImplementedError('Impossible')
                list_i.append(value_i)
            # END-FOR (bank)
            param_table_list.append(list_i)
        # END-FOR

        # convert 2D list to array
        param_array = numpy.array(param_table_list)
        # sort by time
        param_array.view('float, float, float').sort(order=['f0'], axis=0)
        # get returned value
        vec_time = param_array[:, 0]

        # define return data structure
        peak_value_bank_dict = dict()
        for index, bank_id in enumerate(bank_id_list):
            peak_value_bank_dict[bank_id] = param_array[:, index+1]

        return vec_time, peak_value_bank_dict

    def integrate_peaks(self, accumulated_workspace_list, d_min, d_max, norm_by_vanadium,
                        append_mode):
        """ integrate peaks for a list of
        :param accumulated_workspace_list: 
        :param d_min:
        :param d_max:
        :param norm_by_vanadium
        :param append_mode
        :return: 
        """
        if append_mode:
            #
            raise RuntimeError('Need to check whether the peaks have been integrated and'
                               ' recorded')

        # the last workspace might be partially accumulated
        calculated_ws_list = sorted(self._peakIntensityDict.keys())[:-1]

        # loop round all the input workspaces
        for ws_name in accumulated_workspace_list:
            # do not touch the workspaces that already have peak integrated
            if ws_name in calculated_ws_list:
                continue
            if ws_name is None:
                continue

            # get workspace
            workspace_i = mantid_helper.retrieve_workspace(ws_name, True)

            position_list = list()
            intensity_list = list()
            # calculate peak intensity
            for iws in range(workspace_i.getNumberHistograms()):
                value_tup = self.calculate_live_peak_parameters(ws_name=ws_name, bank_id=iws+1,
                                                                norm_by_van=norm_by_vanadium,
                                                                d_min=d_min, d_max=d_max)
                intensity_i = value_tup[0]
                intensity_list.append(intensity_i)

                position_i = value_tup[1]
                position_list.append(position_i)
            # END-FOR (iws)

            # get average time
            time_stamp = workspace_i.run().getProperty('proton_charge').lastTime()

            self._peakIntensityDict[ws_name] = (time_stamp, intensity_list, position_list)
        # END-FOR

        return

    def get_vanadium(self, bank_id):
        # blabla
        return ADS.retrieve(self._vanadiumWorkspaceDict[bank_id]).readY(0)

    # TODO/NOW/ - In-Implementation
    def load_reduced_runs(self, ipts_number, run_number, output_ws_name):
        """

        :param ipts_number:
        :param run_number:
        :return:
        """
        assert isinstance(ipts_number, int), 'blabla2'
        assert isinstance(run_number, int), 'blbbla3'

        gsas_file_name = self._archiveManager.get_data_archive_gsas(ipts_number, run_number)

        mantidsimple.LoadGSS(Filename=gsas_file_name, OutputWorkspace=output_ws_name)

        return

    # TEST TODO/NOW - Method-in-implementation
    def load_smoothed_vanadium(self, van_gsas_file):
        """

        :param van_gsas_file:
        :return:
        """
        # TODO/TODO/NOW/NOW - Clean the code

        # import os
        # gsas_path = os.path.join(os.path.expanduser('~/Downloads/'), '158559-s.gda')
        # general
        mantidsimple.LoadGSS(Filename=van_gsas_file, OutputWorkspace='vanadium')
        mantidsimple.EditInstrumentGeometry(Workspace='vanadium', PrimaryFlightPath=43.753999999999998, SpectrumIDs='1-3',
                               L2='2,2,2', Polar='90,270,150')
        mantidsimple.ConvertUnits(InputWorkspace='vanadium', OutputWorkspace='vanadium', Target='dSpacing')

        # bank 1 and 2
        for bank in [1, 2]:
            ws_name = 'van_bank_{0}'.format(bank)
            mantidsimple.ExtractSpectra(InputWorkspace='vanadium', OutputWorkspace='van2banks', WorkspaceIndexList=bank-1)
            mantidsimple.Rebin(InputWorkspace='van2banks', OutputWorkspace='van2banks', Params='0.3,-0.001, 3.5')
            mantidsimple.FFTSmooth(InputWorkspace='van2banks', OutputWorkspace=ws_name, Filter='Butterworth', Params='20,2',
                  IgnoreXBins=True, AllSpectra=True)
            self._vanadiumWorkspaceDict[bank] = ws_name

        # bank3
        for bank in [3]:
            # special processing for bank 3
            mantidsimple.ExtractSpectra(InputWorkspace='vanadium', OutputWorkspace='vanhighbank', WorkspaceIndexList=bank-1)

            # sort the bins
            bank3ws = ADS.retrieve('vanhighbank')
            vecx = bank3ws.readX(0)
            vecy = bank3ws.readY(0)
            xy_list = list()
            for i in range(len(vecy)):
                xy_list.append((vecx[i], vecy[i]))

            xy_list.sort()

            vec_x = numpy.ndarray(shape=(len(vecx),), dtype='float')
            vec_y = numpy.ndarray(shape=(len(vecy),), dtype='float')

            for i, xy in enumerate(xy_list):
                vec_x[i] = xy[0]
                vec_y[i] = xy[1]
            vec_x[-1] = vecx[-1]

            mantidsimple.CreateWorkspace(DataX=vec_x, DataY=vec_y, NSpec=1, UnitX='dSpacing', OutputWorkspace='vanbank3')

            mantidsimple.Rebin(InputWorkspace='vanbank3', OutputWorkspace='vanbank3', Params='0.3,-0.001, 3.5')
            ws_name = 'van_bank_{0}'.format(bank)
            mantidsimple.FFTSmooth(InputWorkspace='vanbank3', OutputWorkspace=ws_name, WorkspaceIndex=0, Filter='Butterworth',
                  Params='20,2', IgnoreXBins=True, AllSpectra=True)

            self._vanadiumWorkspaceDict[bank] = ws_name
        # END-FOR

        return

    @staticmethod
    def parse_sample_log(ws_name_list, sample_log_name):
        """parse the sample log time stamps and value from a series of workspaces
        :except RuntimeError:
        :param ws_name_list:
        :param sample_log_name:
        :return: date time vector, sample value vector, last time (kernel.DateAndTime)
        """
        # check inputs
        assert isinstance(ws_name_list, list), 'Workspace names {0} must be given as a list but not a {1}.' \
                                               ''.format(ws_name_list, type(ws_name_list))
        assert isinstance(sample_log_name, str), 'Sample log name {0} must be a string but not a {1}.' \
                                                 ''.format(sample_log_name, type(sample_log_name))

        date_time_vec = None
        sample_value_vec = None

        last_time = None
        for seq_index, ws_name in enumerate(ws_name_list):
            if ADS.doesExist(ws_name) is False:
                raise RuntimeError('Workspace {0} does not exist.'.format(ws_name))

            temp_workspace = ADS.retrieve(ws_name)
            time_series = temp_workspace.run().getProperty(sample_log_name)

            time_vec_i = time_series.times
            value_vec_i = time_series.value

            if date_time_vec is None:
                # first workspace to process
                date_time_vec = time_vec_i
                sample_value_vec = value_vec_i
            else:
                # in append mode
                # check
                if date_time_vec[-1] >= time_vec_i[0]:
                    raise RuntimeError('Previous workspace {0} is later than the current one {1}.'
                                       ''.format(ws_name_list[seq_index-1], ws_name))

                # append
                numpy.append(date_time_vec, time_vec_i)
                numpy.append(sample_value_vec, value_vec_i)
            # END-IF-ELSE

            # DEBUG OUTPUT
            print '[DB...SEVERE] Workspace {0} Entry 0: {1} ({2}); Entry -1: {3} ({4}); Number of Entries: {5}' \
                  ''.format(ws_name, time_vec_i[0], time_vec_i[0].totalNanoseconds(),
                            time_vec_i[-1], time_vec_i[-1].totalNanoseconds(), len(time_vec_i))

            last_time = temp_workspace.run().getProperty('proton_charge').lastTime()
        # END-FOR (workspaces)

        return date_time_vec, sample_value_vec, last_time

    @staticmethod
    def sum_workspaces(workspace_name_list, target_workspace_name):
        """
        sum 2 workspaces together
        example: [self._inAccumulationWorkspaceName, workspace_i],  self._inAccumulationWorkspaceName)
        :param workspace_name_list:
        :param target_workspace_name:
        :return: None or warning message
        """
        # check whether inputs are valid
        assert isinstance(workspace_name_list, list), 'Workspace names {0} must be given in list but not {1}.' \
                                                      ''.format(workspace_name_list, type(workspace_name_list))
        assert isinstance(target_workspace_name, str), 'Target workspace name {0} for summed workspaces must be of ' \
                                                       'type {1}'.format(target_workspace_name,
                                                                         type(target_workspace_name))

        if len(workspace_name_list) != 2:
            raise RuntimeError('Sum workspaces must have 2 inputs')

        # plus
        mantidsimple.Plus(LHSWorkspace=workspace_name_list[0], RHSWorkspace=workspace_name_list[1],
                          OutputWorkspace=target_workspace_name)

        # set the run number correctly
        left_ws = ADS.retrieve(workspace_name_list[0])
        right_ws = ADS.retrieve(workspace_name_list[1])
        left_run_number = left_ws.getRunNumber()
        right_run_number = right_ws.getRunNumber()
        target_ws = ADS.retrieve(target_workspace_name)

        return_value = None
        if left_run_number == right_run_number:
            # same so do nothing
            pass
        elif left_run_number == 0:
            # one with run 0 and one is different
            target_ws.getRun().addProperty('run_number', right_run_number, replace=True)
        else:
            # they are different... warning
            return_value = 'Workspaces to sum have 2 different run numbers {0} and {1}.' \
                           ''.format(left_run_number, right_run_number)
            print ('[WARNING] {0}'.format(return_value))
        # END-IF

        return return_value

    def run(self):
        """ main method to start live data
        :return:
        """
        # Test for script: whatever has all the log information...
        # and output_1, output_2 will do good still
        mantidsimple.StartLiveData(UpdateEvery=10,
                                   Instrument='VULCAN',
                                   Listener='SNSLiveEventDataListener',
                                   Address='bl7-daq1.sns.gov:31415',
                                   StartTime='1990-01-01T00:00:00',
                                   ProcessingScriptFilename=self._live_reduction_script,
                                   PreserveEvents=False,
                                   AccumulationMethod='Add',
                                   RunTransitionBehavior='Rename',
                                   OutputWorkspace='VULCAN_Live')

        return

    def stop(self):
        """

        :return:
        """
        AlgorithmManager.cancelAll()

        self._thread_continue = False

        return


def main():
    driver = LiveDataDriver()
    driver.start_live_data()


if __name__ == '__main__':
    main()