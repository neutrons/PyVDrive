# Chop data to 5 seconds and reduce to GSAS
# Test case: run = 160989, duration = 0.69 hour
import time
from mantid.simpleapi import Load, GenerateEventsFilter, FilterEvents, LoadDiffCal, AlignAndFocusPowder, Rebin, AlignDetectors, ConvertUnits
from mantid.simpleapi import DiffractionFocussing, CreateEmptyTableWorkspace, CreateWorkspace, SaveVulcanGSS
import threading
import numpy
from mantid.api import AnalysisDataService
import os
import h5py
import time


# chop data
ipts = 18522
run_number = 160560

# event_file_name = '/SNS/VULCAN/IPTS-13924/nexus/VULCAN_160989.nxs.h5'
# event_file_name = '/SNS/VULCAN/IPTS-{0}/nexus/VULCAN_{1}.nxs.h5'.format(ipts, run_number)
# event_file_name = '/SNS/VULCAN/IPTS-19577/nexus/VULCAN_155771.nxs.h5'

# TODO FIXME - In order to make mutex work... It is necessary to write everything in a class


_SAVEGSS_MUTEX = False


class SliceFocusVulcan(object):
    """

    """
    def __init__(self):
        return

    @staticmethod
    def create_bin_table(num_banks, not_align_idl, h5_bin_file_name=None, binning_parameters=None):
        """
        create a TableWorkspace with binning information
        :param not_align_idl:
        :param data_ws:
        :param h5_bin_file_name:
        :param binning_parameters:
        :return:
        """

        def generate_binning_table(table_name):
            """
            generate an EMPTY binning TableWorkspace
            :param table_name:
            :return:
            """
            bin_table = CreateEmptyTableWorkspace(OutputWorkspace=table_name)
            bin_table.addColumn('str', 'indexes')
            bin_table.addColumn('str', 'params')

            return bin_table

        def extrapolate_last_bin(bins):
            """
            :param bins:
            :return:
            """
            assert isinstance(bins, numpy.ndarray) and len(bins.shape) == 1, '{0} must be a 1D array but not {1}.' \
                                                                             ''.format(bins, type(bins))

            delta_bin = (bins[-1] - bins[-2]) / bins[-2]
            next_bin = bins[-1] * (1 + delta_bin)

            return next_bin

        if not_align_idl:
            # not aligned IDL
            assert isinstance(binning_parameters, list) or isinstance(binning_parameters, tuple), \
                'Binning parameters must be either tuple of list'
            assert len(binning_parameters) == 2, 'Must have both low resolution and high resolution'

            # create binning table
            bin_table_name = 'VULCAN_Binning_Table_{0}Banks'.format(num_banks)
            # if AnalysisDataService.doesExist(bin_table_name) is False:  FIXME how to avoid duplicate operation?
            bin_table_ws = generate_binning_table(bin_table_name)
            east_west_binning_parameters, high_angle_binning_parameters = binning_parameters

            if num_banks == 3:
                # west(1), east(1), high(1)
                bin_table_ws.addRow(['0, 1', '{0}'.format(east_west_binning_parameters)])
                bin_table_ws.addRow(['2', '{0}'.format(high_angle_binning_parameters)])
            elif num_banks == 7:
                # west (3), east (3), high (1)
                bin_table_ws.addRow(['0-5', '{0}'.format(east_west_binning_parameters)])
                bin_table_ws.addRow(['6', '{0}'.format(high_angle_binning_parameters)])
            elif num_banks == 27:
                # west (3), east (3), high (1)
                bin_table_ws.addRow(['0-17', '{0}'.format(east_west_binning_parameters)])
                bin_table_ws.addRow(['18-26', '{0}'.format(high_angle_binning_parameters)])
            else:
                raise RuntimeError('{0} spectra workspace is not supported!'.format(num_banks))

        else:
            # use explicitly defined bins and thus matrix workspace is required
            # import h5 file
            base_table_name = os.path.basename(h5_bin_file_name).split('.')[0]

            # load vdrive bin file to 2 different workspaces
            bin_file = h5py.File(h5_bin_file_name, 'r')
            low_bins = bin_file['west_east_bank'][:]
            high_bins = bin_file['high_angle_bank'][:]
            bin_file.close()

            # append last value for both east/west bin and high angle bin
            low_bins = numpy.append(low_bins, extrapolate_last_bin(low_bins))
            high_bins = numpy.append(high_bins, extrapolate_last_bin(high_bins))

            low_bin_ws_name = '{0}_LowResBin'.format(base_table_name)
            high_bin_ws_name = '{0}_HighResBin'.format(base_table_name)
            if AnalysisDataService.doesExist(low_bin_ws_name) is False:
                CreateWorkspace(low_bins, low_bins, NSpec=1, OutputWorkspace=low_bin_ws_name)
            if AnalysisDataService.doesExist(high_bin_ws_name) is False:
                CreateWorkspace(high_bins, high_bins, NSpec=1, OutputWorkspace=high_bin_ws_name)

            # create binning table name
            bin_table_name = '{0}_{1}Bank'.format(base_table_name, num_banks)

            # no need to create this workspace again and again
            if AnalysisDataService.doesExist(bin_table_name):
                return bin_table_name

            # create binning table
            ref_bin_table = generate_binning_table(bin_table_name)

            if num_banks == 3:
                # west(1), east(1), high(1)
                ref_bin_table.addRow(['0, 1', '{0}: {1}'.format(low_bin_ws_name, 0)])
                ref_bin_table.addRow(['2', '{0}: {1}'.format(high_bin_ws_name, 0)])
            elif num_banks == 7:
                # west (3), east (3), high (1)
                ref_bin_table.addRow(['0-5', '{0}: {1}'.format(low_bin_ws_name, 0)])
                ref_bin_table.addRow(['6', '{0}: {1}'.format(high_bin_ws_name, 0)])
            elif num_banks == 27:
                # west (3), east (3), high (1)
                ref_bin_table.addRow(['0-17', '{0}: {1}'.format(low_bin_ws_name, 0)])
                ref_bin_table.addRow(['18-26', '{0}: {1}'.format(high_bin_ws_name, 0)])
            else:
                raise RuntimeError('{0} spectra workspace is not supported!'.format(num_banks))
        # END-IF-ELSE

        return bin_table_name

    def reduce_data(self, ws_name_list, bin_table_name, ipts_number, gsas_iparm_file_name):
        """
        focus data on a list workspaces
        :param ws_name_list:
        :return:
        """

        print ('Workspaces to reduce: {0}'.format(ws_name_list))
        for ws_name in ws_name_list:
            if len(ws_name) == 0:
                continue
            ConvertUnits(InputWorkspace=ws_name, OutputWorkspace=ws_name, Target='dSpacing')
            DiffractionFocussing(InputWorkspace=ws_name, OutputWorkspace=ws_name, GroupingWorkspace='vulcan_group')
            ConvertUnits(InputWorkspace=ws_name, OutputWorkspace=ws_name, Target='TOF', ConvertFromPointData=False)
            gsas_file_name = '/tmp/{0}.gda'.format(ws_name)

            # while _SAVEGSS_MUTEX is False:
            #     time.sleep(0.0001)
            # _SAVEGSS_MUTEX = True
            # SaveVulcanGSS(InputWorkspace=ws_name,
            #               BinningTable=bin_table_name,
            #               OutputWorkspace=ws_name,
            #               GSSFilename=gsas_file_name,
            #               IPTS=ipts_number,
            #               GSSParmFileName=gsas_iparm_file_name)
            # _SAVEGSS_MUTEX = False

        return

    def chop_focus_save(self, event_file_name, event_ws_name, split_ws_name, info_ws_name,
                        output_ws_base, idl_bin_file_name, east_west_binning_parameters,
                        high_angle_binning_parameters):

        t0 = time.time()
        # Load event file
        Load(Filename=event_file_name, OutputWorkspace=event_ws_name)

        # Load diffraction calibration file
        LoadDiffCal(InputWorkspace=event_ws_name,
                    Filename='/SNS/VULCAN/shared/CALIBRATION/2018_4_11_CAL/VULCAN_calibrate_2018_04_12.h5',
                    WorkspaceName='Vulcan')

        # Align detectors
        AlignDetectors(InputWorkspace=event_ws_name,
                       OutputWorkspace=event_ws_name,
                       CalibrationWorkspace='Vulcan_cal')

        t1 = time.time()

        # time_bin = 300
        # time_bin = 60
        # GenerateEventsFilter(InputWorkspace='ws', OutputWorkspace='MatrixSlicer',
        #                      InformationWorkspace='MatrixInfoTable',
        #                      FastLog=True, TimeInterval=time_bin)

        # Filter events
        result = FilterEvents(InputWorkspace=event_ws_name,
                              SplitterWorkspace=split_ws_name, InformationWorkspace=info_ws_name,
                              OutputWorkspaceBaseName=output_ws_base,
                              FilterByPulseTime=False, GroupWorkspaces=True,
                              OutputWorkspaceIndexedFrom1=True,
                              SplitSampleLogs=True)

        print ('[DB...BAT] There are {0} returned objects from FilterEvents.'.format(len(result)))
        output_names = None
        for r in result:
            if isinstance(r, int):
                print r
            elif isinstance(r, list):
                output_names = r
            else:
                continue
                # print r.name(), type(r)
        print ('Output names: {0}'.format(output_names))

        t2 = time.time()

        # Load calibration
        ws_name_0 = output_names[0]

        # Now start to use multi-threading
        num_outputs = len(output_names)
        num_threads = 16
        half_num = int(num_outputs / num_threads)

        # create binning table
        num_banks = 3
        not_align_idl = False
        bin_table_name = self.create_bin_table(num_banks, not_align_idl,
                                               idl_bin_file_name,
                                               (east_west_binning_parameters, high_angle_binning_parameters))

        thread_pool = dict()
        _SAVEGSS_MUTEX = False
        for thread_id in range(num_threads):
            start = thread_id * half_num
            end = min(start + half_num, num_outputs)
            thread_pool[thread_id] = threading.Thread(target=self.reduce_data,
                                                      args=(output_names[start:end], bin_table_name,
                                                            12345, 'test.prm',))
            thread_pool[thread_id].start()
            print ('thread {0}: [{1}: {2})'.format(thread_id, start, end))

        for thread_id in range(num_threads):
            thread_pool[thread_id].join()

        for thread_id in range(num_threads):
            thread_i = thread_pool[thread_id]
            if thread_i is not None and thread_i.isAlive():
                thread_i._Thread_stop()

        tf = time.time()

        print ('{0}: Runtime = {1}   Total output workspaces = {2}'
               ''.format(event_file_name, tf - t0, len(output_names)))
        print ('Details for thread = {3}:\n\tLoading  = {0}\n\tChopping = {1}\n\tFocusing = {2}'
               ''.format(t1 - t0, t2 - t1, tf - t2, num_threads))

        return



# t1 = threading.Thread(target=reduce_data, args=(output_names[:half_num], ))
# t2 = threading.Thread(target=reduce_data, args=(output_names[half_num:],))
# t1.start()
# t2.start()
# t1.join()
# t2.join()


# # # reduce
# for ws_name in output_names:
#     ConvertUnits(InputWorkspace=ws_name, OutputWorkspace=ws_name, Target='dSpacing')
#     DiffractionFocussing(InputWorkspace=ws_name, OutputWorkspace=ws_name, GroupingWorkspace='vulcan_group')
#     ConvertUnits(InputWorkspace=ws_name, OutputWorkspace=ws_name, Target='TOF', ConvertFromPointData=False)
#     # Rebin(InputWorkspace=ws_name, OutputWorkspace=ws_name, Params='5000,-0.001,50000', FullBinsOnly=True)


# /SNS/VULCAN/IPTS-19577/nexus/VULCAN_155771.nxs.h5: Runtime = 226.181304932   Total output workspaces = 733
# Details for thread = 32:
# 	Loading  = 97.1458098888
# 	Chopping = 35.0766251087
# 	Focusing = 93.9588699341


