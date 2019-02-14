import os
import sys

# # path will be ... TODO TODO TODO
# sys.path.append('/SNS/users/wzz/Mantid_Project/builds/build-vulcan/bin')


import numpy
import mantid.simpleapi as mantidsimple
import mantid
from mantid.api import AlgorithmManager
from mantid.api import AnalysisDataService as ADS
import mantid_helper
import peak_util
import archivemanager
try:
    from PyQt5 import QtCore
except ImportError:
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

    if os.path.exists('/SNS/VULCAN/'):
        LIVE_PROCESS_SCRIPTS = '/SNS/VULCAN/shared/livereduce/vulcan_live_data_v0_9.py'
    elif os.path.exists('/home/bl-user/.pyvdrive/vulcan_live_data_v0_9.py'):
        LIVE_PROCESS_SCRIPTS = '/home/bl-user/.pyvdrive/vulcan_live_data_v0_9.py'
    else:
        LIVE_PROCESS_SCRIPTS = '/SNS/users/wzz/VULCAN/shared/livereduce/vulcan_live_data_v0_9.py'

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
        self._peakMinD = None
        self._peakMaxD = None
        self._peakNormByVan = False
        # _peakParamDict: key = %.5f %.5f %d % (min-d, max-d, norm-by-van):  value: dictionary
        #   level-2 dict: key: workspace name, value: dictionary for bank 1, bank 2, bank 3, time
        #   level-3 dict: key: bank ID, value: 3-tuple as peak intensity, peak center, variance
        self._peakParamDict = dict()
        self._currPeakParamKey = None

        self._vanadiumWorkspaceDict = dict()  # key: bank ID.  value: workspace name

        return

    @staticmethod
    def _get_peak_key(d_min, d_max, norm_by_vanadium):
        """
        a standard method to generate key for _peakParamDict
        :param d_min:
        :param d_max:
        :param norm_by_vanadium:
        :return:
        """
        key = '%.5f %.5f %d' % (d_min, d_max, norm_by_vanadium)

        return key

    def calculate_live_peak_parameters(self, ws_name, bank_id, norm_by_van, d_min, d_max):
        """ calculate the peak parameters in live data
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
        assert isinstance(bank_id, int), 'Bank ID {0} must be an integer but not a {1}.'.format(bank_id, type(bank_id))

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
    def convert_time_stamps(date_time_vec, time_shift):
        """convert a vector of DateAndTime instance to a vector of double as relative
        time to a specified time in DateAndTime
        :param date_time_vec:
        :param time_shift: start time
        :return: a vector of time stamps in double/float in unit of seconds
        """
        # check inputs
        assert isinstance(date_time_vec, numpy.ndarray), 'Input time vector must be a numpy.array but not a {0}.' \
                                                         ''.format(type(date_time_vec))
        assert isinstance(time_shift, numpy.datetime64), 'Relative time {0} must be a numpy.datetime64 instance ' \
                                                         'but not a {1}.'.format(time_shift, type(time_shift))

        # create an array
        shape = len(date_time_vec)
        time_vec = numpy.ndarray(shape=(shape,), dtype='float')

        # convert
        for i in range(shape):
            time_i = (date_time_vec[i] - time_shift).tolist() * 1.E-9
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

    # TODO - TONIGHT 3 - Consider to remove since mantid_helper is used
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
    def get_data_from_workspace(workspace_name, bank_id=None, target_unit=None, starting_bank_id=1):
        """
        get data from a workspace
        :param workspace_name:
        :param bank_id:
        :param target_unit: None for using current unit
        :param starting_bank_id: lowest bank ID
        :return: 2-tuple as (boolean, returned object); boolean as status of executing the method
                 if status is False, returned object is a string for error message
                 if status is True and Bank ID is None: returned object is a dictionary with all Bank IDs
                 if status is True and Bank ID is not None: returned object is a dictionary with the specified bank ID.
                 The value of each entry is a tuple with vector X, vector Y and vector Z all in numpy.array
        """
        try:
            data_set_dict, curr_unit = mantid_helper.get_data_from_workspace(workspace_name,
                                                                             bank_id=bank_id,
                                                                             target_unit=target_unit,
                                                                             start_bank_id=starting_bank_id)
        except RuntimeError as run_err:
            return False, str(run_err)

        return True, (data_set_dict, curr_unit)

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

    def get_peaks_parameters(self, param_type, bank_id_list, time0, d_min=None, d_max=None, norm_by_vanadium=None):
        """
        get the peaks' positions (calculated) along with time
        :param param_type:
        :param bank_id_list: bank IDs
        :param time0: starting time for time stamps
        :param d_min:
        :param d_max:
        :param norm_by_vanadium:
        :return:
        """
        # check whether inputs are valid
        assert isinstance(bank_id_list, list), 'Bank ID list {0} must be an integer but not a {1}.' \
                                               ''.format(bank_id_list, type(bank_id_list))
        assert isinstance(param_type, str), 'Peak parameter type {0} must be a string but not a {1}.' \
                                            ''.format(param_type, type(param_type))
        assert isinstance(time0, numpy.datetime64), 'Time0 {0} must be of type datetime64 but not {1}.' \
                                                    ''.format(time0, type(time0))

        # get peak type
        if param_type == 'center':
            type_index = 1
        elif param_type == 'intensity':
            type_index = 0
        else:
            raise RuntimeError('Peak parameter type {0} is not recognized. Supported are "center" and "intensity"'
                               ''.format(param_type))

        # get key:
        if d_min is not None and d_max is not None and norm_by_vanadium is not None:
            peak_key = self._get_peak_key(d_min, d_max, norm_by_vanadium)
        else:
            peak_key = self._currPeakParamKey

        # parse data to numpy array
        # assuming that there are 3 banks  FIXME - make it general for more than 3 banks
        num_pts = len(self._peakParamDict[peak_key])
        dim = 1 + len(bank_id_list)
        param_matrix = numpy.ndarray(shape=(num_pts, dim), dtype='float')  # time, b1, b2, b3
        for index, value_dict in enumerate(self._peakParamDict[peak_key].values()):
            time_i = value_dict['time']
            time_i_rel = (time_i - time0).tolist() * 1.E-9  # convert from nanosecond to second
            param_matrix[index][0] = time_i_rel
            for col_index, bank_id in enumerate(bank_id_list):
                value_i = value_dict[bank_id][type_index]
                param_matrix[index][col_index+1] = value_i
            # END-FOR
        # END-FOR

        # sort by time
        view_format =  str(['float'] * (1 + len(bank_id_list))).replace('[', '').replace(']', '').replace('\'', '')
        # example: 'float, float, float, float'
        param_matrix.view(view_format).sort(order=['f0'], axis=0)
        # get returned value
        vec_time = param_matrix[:, 0]

        # define return data structure
        peak_value_bank_dict = dict()
        for index, bank_id in enumerate(bank_id_list):
            peak_value_bank_dict[bank_id] = param_matrix[:, index+1]

        return vec_time, peak_value_bank_dict

    def integrate_peaks(self, accumulated_workspace_list, d_min, d_max, norm_by_vanadium):
        """ integrate peaks for a list of
        :param accumulated_workspace_list: 
        :param d_min:
        :param d_max:
        :param norm_by_vanadium
        :return:
        """
        # check inputs
        assert isinstance(accumulated_workspace_list, list), 'Accumulated workspace {0} must be given in a list but ' \
                                                             'not by a {1}.'.format(accumulated_workspace_list,
                                                                                    type(accumulated_workspace_list))
        assert isinstance(d_min, float), 'Min dSpacing {0} must be a float but not a {1}'.format(d_min, type(d_min))
        assert isinstance(d_max, float), 'Max dSpacing {0} must be a float but not a {1}'.format(d_max, type(d_max))
        assert isinstance(norm_by_vanadium, bool), 'Flag to normalize by vanadium shall be a boolean'

        # determine whether it shall be in appending mode or new calculation mode
        peak_key = self._get_peak_key(d_min, d_max, norm_by_vanadium)
        if peak_key not in self._peakParamDict:
            self._peakParamDict[peak_key] = dict()
            # key: workspace name, value: dictionary for bank 1, bank 2, bank 3 and time
        # update for the current peak parameter dictionary key
        self._currPeakParamKey = peak_key

        # the last workspace might be partially accumulated
        last_workspace_name = sorted(accumulated_workspace_list)[-1]

        for ws_name in accumulated_workspace_list:
            if ws_name is None:
                # workspace name is None or not exist?
                print '[WARNING] Found workspace None in given accumulated workspaces {0}' \
                      ''.format(accumulated_workspace_list)
                continue

            # integrate peak for the non-integrated workspace and LAST workspace only
            if ws_name in self._peakParamDict[peak_key] and ws_name != last_workspace_name:
                # integrated + not the last one
                continue

            # too old to be in ADS
            if mantid_helper.workspace_does_exist(ws_name) is False:
                print '[WARNING] Workspace {0} does not exist in ADS.'.format(ws_name)
                continue

            # get workspace
            workspace_i = mantid_helper.retrieve_workspace(ws_name, True)

            # calculate peak intensity
            self._peakParamDict[peak_key][ws_name] = dict()
            for iws in range(workspace_i.getNumberHistograms()):
                value_tup = self.calculate_live_peak_parameters(ws_name=ws_name, bank_id=iws+1,
                                                                norm_by_van=norm_by_vanadium,
                                                                d_min=d_min, d_max=d_max)
                bank_id = iws + 1
                self._peakParamDict[peak_key][ws_name][bank_id] = value_tup
                # intensity_i = value_tup[0]
                # intensity_list.append(intensity_i)
                #
                # position_i = value_tup[1]
                # position_list.append(position_i)
            # END-FOR (iws)

            # get latest time
            time_stamp = workspace_i.run().getProperty('proton_charge').times[-1]
            self._peakParamDict[peak_key][ws_name]['time'] = time_stamp
        # END-FOR

        return

    def get_vanadium(self, bank_id):
        """
        get vanadium spectrum of a bank ID
        :param bank_id:
        :return:
        """
        # check input
        assert isinstance(bank_id, int), 'Bank ID {0} must be an integer but not a {1}.' \
                                         ''.format(bank_id, type(bank_id))
        if bank_id not in self._vanadiumWorkspaceDict:
            raise RuntimeError('Bank ID {0} does not exist in vanadium workspaces. Current supported are {1}'
                               ''.format(bank_id, self._vanadiumWorkspaceDict.keys()))

        return ADS.retrieve(self._vanadiumWorkspaceDict[bank_id]).readY(0)

    # def load_reduced_runs(self, ipts_number, run_number, output_ws_name):
    #     """
    #
    #     :param ipts_number:
    #     :param run_number:
    #     :return:
    #     """
    #     assert isinstance(ipts_number, int), 'IPTS number {0} ({1}) must be an integer.' \
    #                                          ''.format(ipts_number, type(ipts_number))
    #     assert isinstance(run_number, int), 'Run number {0} ({1}) must be an integer.' \
    #                                         ''.format(run_number, type(run_number))
    #
    #     # TODO/ASAP/ - In-Implementation
    #
    #     gsas_file_name = self._archiveManager.locate_gsas(ipts_number, run_number)
    #
    #     mantidsimple.LoadGSS(Filename=gsas_file_name, OutputWorkspace=output_ws_name)
    #
    #     return

    def load_smoothed_vanadium(self, van_gsas_file):
        """ Load smoothed vanadium spectra from GSAS file
        :param van_gsas_file:
        :return:
        """
        # check
        assert isinstance(van_gsas_file, str), 'Vanadium GSAS file name {0} must be a string.'.format(van_gsas_file)
        if os.path.exists(van_gsas_file) is False:
            raise RuntimeError('Vanadium GSAS file {0} cannot be found.'.format(van_gsas_file))

        # load file and edit instrument for dSpacing
        mantidsimple.LoadGSS(Filename=van_gsas_file, OutputWorkspace='vanadium')   # 3 banks
        mantidsimple.EditInstrumentGeometry(Workspace='vanadium', PrimaryFlightPath=43.753999999999998,
                                            SpectrumIDs='1, 2, 3',
                                            L2='2,2,2', Polar='-90,90,155')
        mantidsimple.ConvertUnits(InputWorkspace='vanadium', OutputWorkspace='vanadium', Target='dSpacing')

        # bank 1 and 2: extract, rebin and smooth
        for bank in [1, 2]:
            ws_name = 'van_bank_{0}'.format(bank)
            mantidsimple.ExtractSpectra(InputWorkspace='vanadium', OutputWorkspace='van2banks',
                                        WorkspaceIndexList=bank-1)
            mantidsimple.Rebin(InputWorkspace='van2banks', OutputWorkspace='van2banks',
                               Params='0.3,-0.001, 3.5')
            mantidsimple.FFTSmooth(InputWorkspace='van2banks', OutputWorkspace=ws_name,
                                   Filter='Butterworth', Params='20,2',
                                   IgnoreXBins=True, AllSpectra=True)
            self._vanadiumWorkspaceDict[bank] = ws_name
        # END-FOR
        mantid_helper.delete_workspace('van2banks')

        # bank3: different algorithm because it has more bins than bank 1 and 2 but has some issue with Mantid
        for bank in [3]:
            # special processing for bank 3
            mantidsimple.ExtractSpectra(InputWorkspace='vanadium', OutputWorkspace='vanhighbank',
                                        WorkspaceIndexList=bank-1)

            # sort the bins: FIXME might be better to use numpy array
            bank3ws = ADS.retrieve('vanhighbank')
            vecx = bank3ws.readX(0)
            vecy = bank3ws.readY(0)
            xy_list = list()
            for i in range(len(vecy)):
                xy_list.append((vecx[i], vecy[i]))

            # X might be out of order
            xy_list.sort()

            vec_x = numpy.ndarray(shape=(len(vecx),), dtype='float')
            vec_y = numpy.ndarray(shape=(len(vecy),), dtype='float')

            for i, xy in enumerate(xy_list):
                vec_x[i] = xy[0]
                vec_y[i] = xy[1]
            vec_x[-1] = vecx[-1]

            # re-create workspace
            mantidsimple.CreateWorkspace(DataX=vec_x, DataY=vec_y, NSpec=1,
                                         UnitX='dSpacing', OutputWorkspace='vanbank3')
            mantidsimple.Rebin(InputWorkspace='vanbank3', OutputWorkspace='vanbank3', Params='0.3,-0.001, 3.5')
            ws_name = 'van_bank_{0}'.format(bank)
            mantidsimple.FFTSmooth(InputWorkspace='vanbank3', OutputWorkspace=ws_name, WorkspaceIndex=0,
                                   Filter='Butterworth', Params='20,2', IgnoreXBins=True, AllSpectra=True)

            self._vanadiumWorkspaceDict[bank] = ws_name

            # clean
            mantid_helper.delete_workspace('vanbank3')
            mantid_helper.delete_workspace('vanhighbank')
        # END-FOR

        # make sure there won't be any less than 0 item
        for ws_name in self._vanadiumWorkspaceDict.keys():
            van_bank_i_ws = mantid_helper.retrieve_workspace(self._vanadiumWorkspaceDict[ws_name], True)
            for i in range(len(van_bank_i_ws.readY(0))):
                if van_bank_i_ws.readY(0)[i] < 1.:
                    van_bank_i_ws.dataY(0)[i] = 1.
        # END-FOR

        return

    @staticmethod
    def parse_sample_log(ws_name_list, sample_log_name):
        """parse the sample log time stamps and value from a series of workspaces
        :except RuntimeError:
        :param ws_name_list:
        :param sample_log_name:
        :return: time stamps (ndarray for datetime64), sample values (float vector), last pulse time (numpy.datetime64)
        """
        # check inputs
        assert isinstance(ws_name_list, list), 'Workspace names {0} must be given as a list but not a {1}.' \
                                               ''.format(ws_name_list, type(ws_name_list))
        assert isinstance(sample_log_name, str), 'Sample log name {0} must be a string but not a {1}.' \
                                                 ''.format(sample_log_name, type(sample_log_name))

        date_time_vec = None
        sample_value_vec = None

        last_pulse_time = None
        for seq_index, ws_name in enumerate(ws_name_list):
            if ADS.doesExist(ws_name) is False:
                raise RuntimeError('Workspace {0} does not exist.'.format(ws_name))

            temp_workspace = ADS.retrieve(ws_name)
            time_series = temp_workspace.run().getProperty(sample_log_name)

            time_vec_i = time_series.times  # numpy.ndarray
            value_vec_i = time_series.value

            if date_time_vec is None:
                # first workspace to process
                date_time_vec = time_vec_i
                sample_value_vec = value_vec_i
            else:
                # in append mode
                # check
                if date_time_vec[-1] > time_vec_i[0]:
                    diff_ns = (date_time_vec[-1] - time_vec_i[0]).tolist()
                    error_message = 'Previous workspace {0} is later than the current one {1} on sample log {2}:' \
                                    ' {3} vs {4} by {5}' \
                                    ''.format(ws_name_list[seq_index - 1], ws_name, sample_log_name,
                                              date_time_vec[-1], time_vec_i[0], diff_ns)
                    if ws_name == 'Accumulated_00001':
                        # if it happens with first.. just skip!
                        print '[ERROR] {0}'.format(error_message)
                        continue
                    else:
                        raise RuntimeError(error_message)
                elif date_time_vec[-1] == time_vec_i[0]:
                    print 'Previous workspace {0} has one entry overlapped with current one {1} on sample log {2}: ' \
                          '{3} vs {4}. Values are {5} and {6}.' \
                          ''.format(ws_name_list[seq_index-1], ws_name, sample_log_name,
                                    date_time_vec[-1], time_vec_i[0], sample_value_vec[-1], value_vec_i[0])

                # append
                numpy.append(date_time_vec, time_vec_i)
                numpy.append(sample_value_vec, value_vec_i)
            # END-IF-ELSE

            # DEBUG OUTPUT
            print '[DB...SEVERE] Workspace {0} Entry 0: {1}; Entry -1: {2}; Number of Entries: {3}' \
                  ''.format(ws_name, time_vec_i[0], time_vec_i[-1], len(time_vec_i))

            last_pulse_time = temp_workspace.run().getProperty('proton_charge').times[-1]
        # END-FOR (workspaces)

        return date_time_vec, sample_value_vec, last_pulse_time

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
        print ('[DB...BAT] reduction script: {}'.format(self._live_reduction_script))
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
