import os
import os.path

import mantid_helper
import reductionmanager as prl
import archivemanager


class VDProject(object):
    """ VDrive Project
    """
    def __init__(self, project_name):
        """ Init
        """
        self._name = project_name
        # dictionary for the information of run number, file name and IPTS
        # key: run number, value: 2-tuple (file name, IPTS)
        self._dataFileDict = dict()
        # List of data file's base name
        self._baseDataFileNameList = list()
        # Data path.  With baseDataFileName, a full path to a data set can be constructed
        self._baseDataPath = None
        # dictionary for sample run mapping to vanadium run
        # Key: sample run number of type integer; Value: vanadium run number in type of integer
        self._sampleRunVanadiumDict = dict()

        # Data structure to manage split run: key run number or file name
        self._splitWorkspaceDict = dict()

        # Reduction manager
        # FIXME - Need to make the setup of instrument more flexible.
        self._reductionManager = prl.ReductionManager(instrument='VULCAN')
        # dictionary for sample run number to be flagged to reduce.
        # Key: run number. Value: boolean flag for reduction
        self._sampleRunReductionFlagDict = dict()
        
        return

    def _clear_split_run(self, run_number):
        """
        Clear splitted workspace of a run
        :param run_number:
        :return:
        """
        # Check
        if run_number not in self._splitWorkspaceDict:
            return False, 'Run number %d has not split workspaces.' % run_number

        # Delete workspaces
        num_ws = len(self._splitWorkspaceDict[run_number])
        for i_split_ws in xrange(num_ws):
            split_ws = self._splitWorkspaceDict[run_number][num_ws-i_split_ws-1]
            mantid_helper.delete_workspace(split_ws)

        return

    def add_run(self, run_number, file_name, ipts_number):
        """
        Add a run to project
        :param run_number:
        :param file_name:
        :param ipts_number:
        :return:
        """
        # Check input
        assert(isinstance(run_number, int))
        assert(isinstance(ipts_number, int))
        assert(isinstance(file_name, str))

        self._dataFileDict[run_number] = (file_name, ipts_number)

        return

    def add_runs(self, run_info_list):
        """
        List of run-info-dict
        :param run_info_list:
        :return:
        """
        # check
        assert isinstance(run_info_list, list), 'blabla'  # TODO/NOW - doc

        for run_info in run_info_list:
            assert isinstance(run_info, dict)
            run_number = run_info['run']
            ipts_number = run_info['ipts']
            file_name = run_info['file']
            self.add_run(run_number, file_name, ipts_number)

        return

    def chop_data_by_time(self, run_number, start_time, stop_time, time_interval, reduce, output_dir):
        """
        chop data by time and reduce???
        :param run_number:
        :param start_time:
        :param stop_time:
        :param time_interval:
        :return:
        """
        # TODO/ISSUE/51 - doc and check
        assert isinstance(run_number, int), 'blabla'

        # load file
        nxs_file_name = self._dataFileDict[run_number][0]
        ws_name = os.path.basename(nxs_file_name).split('.')[0]
        mantid_helper.load_nexus(nxs_file_name, ws_name, meta_data_only=False)

        # generate event filter
        split_ws_name = 'TimeSplitters_%07d' % run_number
        info_ws_name = 'TimeInfoTable_%07d' % run_number
        status, ret_obj = mantid_helper.generate_event_filters_by_time(ws_name, split_ws_name, info_ws_name,
                                                                       start_time, stop_time, time_interval,
                                                                       time_unit='Seconds')

        if reduce:
            # reduce to GSAS and etc
            import reduce_VULCAN

            reduce_setup = reduce_VULCAN.ReductionSetup()
            reduce_setup.set_event_file(nxs_file_name)
            reduce_setup.set_output_dir(output_dir)
            reduce_setup.set_gsas_dir(output_dir, main_gsas=True)
            reduce_setup.is_full_reduction = False

            # add splitter workspace and splitter information workspace
            reduce_setup.set_splitters(split_ws_name, info_ws_name)

            reducer = reduce_VULCAN.ReduceVulcanData(reduce_setup)
            status, message = reducer.chop_reduce()

        else:
            # just split the workspace and saved in memory
            # TODO/FIXME/NOW - TOF correction should be left to user to specify
            mantid_helper.split_event_data(ws_name, split_ws_name, info_ws_name, ws_name, False)

        return message

    def clear_reduction_flags(self):
        """ Set to all runs' reduction flags to be False
        :return:
        """
        for run_number in self._sampleRunReductionFlagDict.keys():
            self._sampleRunReductionFlagDict[run_number] = False

        return

    def clear_runs(self):
        """
        Purpose:
            Clear memory, i.e., loaded workspace
        Requirements:

        Guarantees:

        :return:
        """
        assert(isinstance(self._dataFileDict, dict))
        self._dataFileDict.clear()

        return

    def deleteData(self, datafilename):
        """ Delete a data file in the project
        """
        self._dataFileDict.remove(datafilename)
        self._baseDataFileNameList.remove(os.path.basename(datafilename))

        return

    def get_file_path(self, run_number):
        """ Get file path
        Purpose: Get the file path from run number
        Requirements: run number is non-negative integer and it has been loaded to Project
        Guarantees: the file path is given
        :param run_number:
        :return:
        """
        assert isinstance(run_number, int) and run_number >= 0

        if run_number in self._dataFileDict:
            file_path = self._dataFileDict[run_number][0]
        else:
            raise RuntimeError('Run %d does not exist in this project.' % run_number)

        return file_path

    def getBaseDataPath(self):
        """ Get the base data path of the project
        """
        return self._baseDataPath

    def get_ipts_runs(self):
        """ Get IPTS numbers and runs
        :return: dictionary of list. Key: ipts number, Value: list of runs belonged to ipts
        """
        ipts_dict = dict()

        for run_number in self._dataFileDict.keys():
            ipts_number = self._dataFileDict[run_number][1]
            if ipts_number not in ipts_dict:
                ipts_dict[ipts_number] = list()
            ipts_dict[ipts_number].append(run_number)
        # END-FOR (run_number)

        # Sort
        for ipts_number in ipts_dict.keys():
            ipts_dict[ipts_number].sort()

        return ipts_dict

    def get_number_data_files(self):
        """
        Get the number/amount of the data files that have been set to the project.
        :return:
        """
        return len(self._dataFileDict)

    def get_number_reduction_runs(self):
        """
        Get the number/amount of the runs that have been reduced.
        :return:
        """
        num_to_reduce = 0
        print '[DB-BAT] ', self._sampleRunReductionFlagDict
        print

        for run_number in self._sampleRunReductionFlagDict.keys():
            if self._sampleRunReductionFlagDict[run_number]:
                num_to_reduce += 1

        return num_to_reduce

    def get_reduced_runs(self):
        """ Get the run/run numbers of the reduced runs
        :return: list of strings
        """
        return self._reductionManager.get_reduced_runs()

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
        assert unit is None or isinstance(unit, str)

        # get reduced workspace name
        reduced_ws_name = self._reductionManager.get_reduced_workspace(run_number, unit)

        # get data
        data_set_dict = mantid_helper.get_data_from_workspace(reduced_ws_name, point_data=True)
        assert isinstance(data_set_dict, dict), 'Returned value from get_data_from_workspace must be a dictionary,' \
                                                'but not %s.' % str(type(data_set_dict))

        return data_set_dict

    def get_reduced_run_history(self, run_number):
        """ Get the processing history of a reduced run
        :param run_number:
        :return:
        """
        # TODO/NOW/1st: think of how to implement!
        return blabla

    def get_reduced_run_information(self, run_number):
        """
        Purpose: Get the reduced run's information including list of banks
        Requirements: run number is an integer
        :param run_number:
        :return: a list of integers as bank ID. reduction history...
        """
        # Check
        assert isinstance(run_number, int), 'Run number must be an integer.'

        # Get workspace
        run_ws_name = self._reductionManager.get_reduced_workspace(run_number)
        ws_info = mantid_helper.get_workspace_information(run_ws_name)

        return ws_info

    def get_run_info(self, run_number):
        """
        Get run's information
        :param run_number:
        :return:  2-tuple (file name, IPTS)
        """
        if self._dataFileDict.has_key(run_number) is False:
            raise RuntimeError('Unable to find run %d in project manager.' % run_number)

        return self._dataFileDict[run_number]

    def get_runs(self):
        """
        Get runs
        :return:
        """
        run_list = self._dataFileDict.keys()
        run_list.sort()
        return run_list

    def getReducedRuns(self):
        """ Get the the list of the reduced runs
        
        Return :: list of data file names 
        """
        return self._myRunPdrDict.keys()

    def has_run(self, run_number):
        """
        Purpose:
            Find out whether a run number is here
        Requirements:
            run number is an integer
        Guarantee:

        :return: boolean as has or not
        """
        assert isinstance(run_number, int)

        do_have = run_number in self._dataFileDict

        return do_have

    def hasData(self, datafilename):
        """ Check whether project has such data file 
        """
        if self._dataFileDict.count(datafilename) == 1:
            # Check data set with full name
            return True
        elif self._baseDataFileNameList.count(datafilename) == 1:
            # Check data set with base name
            return True

        return False

    def load_session_from_dict(self, save_dict):
        """ Load session from a dictionary
        :param save_dict:
        :return:
        """
        assert isinstance(save_dict, dict)

        # Set
        self._name = save_dict['name']
        self._baseDataPath = save_dict['baseDataPath']
        self._dataFileDict = save_dict['dataFileDict']
        self._baseDataFileNameList = save_dict['baseDataFileNameList']

        return

    def mark_runs_to_reduce(self, run_number_list):
        """ Mark runs to reduce
        Purpose:

        Requirements:
            1. run number does exist in this project;
            2. data file of this run is accessible
            3. input run number list must be a list of integer
        Guarantees
        :param run_number_list:
        :return: None
        """
        # Check requirements
        assert isinstance(run_number_list, list)

        # Mark each runs
        for run_number in sorted(run_number_list):
            assert isinstance(run_number, int),\
                'run_number must be of type integer but not %s' % str(type(run_number))
            if self.has_run(run_number) is False:
                # no run
                raise RuntimeError('Run %d cannot be found.' % run_number)
            elif archivemanager.check_read_access(self.get_file_path(run_number)) is False:
                # file does not exist
                raise RuntimeError('Run %d with file path %s cannot be found.' % (run_number,
                                                                                  self.get_file_path(run_number)))
            else:
                # mark runs to reduce
                self._sampleRunReductionFlagDict[run_number] = True
        # END-FOR

        return

    def name(self):
        """ Get name of the project
        :return:
        """
        return self._name

    def reduce_vanadium_runs(self):
        """ Reduce vanadium runs
        Purpose:
            Get or reduce vanadium runs according to the runs that are flagged for reduction
        Requirements:
            There are some vanadium runs that can be found
        Guarantees:
            The corresponding vanadium runs are reduced with the proper binning parameters
        :return:
        """
        # Check requirements
        van_run_number_set = set()
        for sample_run_number in self._sampleRunReductionFlagDict:
            if self._sampleRunReductionFlagDict[sample_run_number] is True:
                assert sample_run_number in self._sampleRunVanadiumDict
                van_run_number = self._sampleRunVanadiumDict[sample_run_number]
                van_run_number_set.add(van_run_number)
        # END-FOR
        assert len(van_run_number_set) > 0, 'There must be at least more than 1 vanadium runs for the sample runs.'

        # Get binning parameters and decide whether to reduce or not
        for van_run_number in van_run_number_set:
            if self._vanadiumRunsManager.has(van_run_number) is False:
                handler = self._reductionManager.reduce_sample_run(van_run_number)
                self._vanadiumRunsManager.set_reduced_vanadium(handler)
            # END-IF
        # END-FOR

        return

    def reduce_runs(self):
        """ Reduce a set of runs without being normalized by vanadium. Mostly align and focus
        Purpose:
        Requirements:
        Guarantees:

        Note:
        1. There is no need to call LoadCalFile explicitly, because AlignAndFocus() will
           check whether the calibration file has been loaded by standard offset and group
           workspace name.

        Migrated from reduceToPDData(self, normByVanadium=True, eventFilteringSetup=None):
        Focus and process the selected data sets to powder diffraction data
        for GSAS/Fullprof/ format

        Workflow:
         1. Get a list of runs to reduce;
         2. Get a list of vanadium runs for them;
         3. Reduce all vanadium runs;
         4. Reduce (and possibly chop) runs;

        Arguments:
         - normByVanadium :: flag to normalize by vanadium

        :return:
        """
        # Load time focusing calibration: there is no need to load time focus calibration
        try:
            self._reductionManager.load_time_focus_calibration()
        except AssertionError, err:
            raise RuntimeError('Unable to load time focus calibration due to %s.' % str(err))

        # Reduce all runs
        for run_number in self._sampleRunReductionFlagDict.keys():
            if self._sampleRunReductionFlagDict[run_number] is True:
                # Initialize trackers
                data_file_name = self._dataFileDict[run_number][0]
                self._reductionManager.init_tracker(run_number, data_file_name)

                # Reduce
                self._reductionManager.reduce_sample_run(run_number)
        # END-FOR

        return True, ''

        print 'Refactor!'
        self._lastReductionSuccess = False

        # Build list of files to reduce
        rundict = {}
        runbasenamelist = []
        for run in self._reductionFlagDict.keys():
            if self._reductionFlagDict[run] is True:
                basenamerun = os.path.basename(run)
                rundict[basenamerun] = (run, None)
                runbasenamelist.append(basenamerun)
        # ENDFOR
        print "[DB] Runs to reduce: %s." % (str(runbasenamelist))
        if len(rundict.keys()) == 0:
            return (False, 'No run is selected to reduce!')

        # Build list of vanadium runs
        vanrunlist = []
        if normByVanadium is True:
            for runbasename in sorted(self._datacalibfiledict.keys()):
                if (runbasename in runbasenamelist) is True:
                    print "[DB] Run %s has vanadium mapped: %s" % (runbasename, str(self._datacalibfiledict[runbasename]))
                    candidlist = self._datacalibfiledict[runbasename][0]
                    if candidlist is None:
                        # no mapped vanadium
                        continue
                    elif isinstance(candidlist, list) is False:
                        # unsupported case
                        raise NotImplementedError("Vanadium candidate list 'candidlist' must be either list or None. \
                                Now it is %s." % (str(candidlist)))
                    vanindex = self._datacalibfiledict[runbasename][1]
                    try:
                        vanrunlist.append(int(candidlist[vanindex]))
                        rundict[runbasename] = (rundict[runbasename][0], int(candidlist[vanindex]))
                    except TypeError as te:
                        print "[Warning] Van run in candidate list is %s.  \
                                Cannot be converted to van run du to %s. " % (str(candidlist[vanindex]), str(te))
                    except IndexError as ie:
                        raise ie
                # ENDIF
            # ENDFOR
            vanrunlist = list(set(vanrunlist))
        # ENDIF
        print "[DB] Vanadium runs (to reduce): %s" % (str(vanrunlist))

        # from vanadium run to create vanadium file
        vanfilenamedict = {}
        for vrun in vanrunlist:
            vanfilename = self._generateFileName(vrun, self._myVanRunIptsDict[int(vrun)])
            vanfilenamedict[int(vrun)] = vanfilename
        # ENDFOR

        # Reduce all vanadium runs
        vanPdrDict = {}
        for vrun in vanrunlist:
            vrunfilename = vanfilenamedict[vrun]
            vpdr = prl.ReductionManager(vrunfilename, isvanadium=True)
            vanws = vpdr.reduce_vanadium_run(params={})
            if vanws is None:
                raise NotImplementedError("Unable to reduce vanadium run %s." % (str(vrun)))
            vanPdrDict[vrun] = vpdr
        # ENDFOR

        # Reduce all
        for basenamerun in sorted(rundict.keys()):
            # reduce regular powder diffraction data
            fullpathfname = rundict[basenamerun][0]
            vanrun = rundict[basenamerun][1]

            runpdr = prl.ReductionManager(fullpathfname, isvanadium=False)

            # optinally chop
            doChopData = False
            if eventFilteringSetup is not None:
                runpdr.setupEventFiltering(eventFilteringSetup)
                doChopData = True
            # ENDIF

            # set up vanadium
            if vanPdrDict.has_key(vanrun) is True and normByVanadium is True:
                vrun = vanPdrDict[vanrun]
            else:
                vrun = None
            # ENDIF (vrun)

            # reduce data
            runpdr.reducePDData(params=prl.PowderReductionParameters(),
                                vrun=vrun,
                                chopdata=doChopData,
                                tofmin=self._tofMin, tofmax=self._tofMax)

            self._myRunPdrDict[basenamerun] = runpdr
        # ENDFOR(basenamerun)

        self._lastReductionSuccess = True

        return (True, '')

    def save_session(self, out_file_name):
        """ Save session to a dictionary
        :param out_file_name:
        :return:
        """
        # Save to a dictionary
        save_dict = dict()
        save_dict['name'] = self._name
        save_dict['dataFileDict'] = self._dataFileDict
        save_dict['baseDataFileNameList'] = self._baseDataFileNameList
        save_dict['baseDataPath'] = self._baseDataPath

        # Return if out_file_name is None
        if out_file_name is None:
            return save_dict

        assert isinstance(out_file_name, str)
        futil.save_xml(save_dict, out_file_name)

        return None

    def set_focus_calibration_file(self, focus_cal_file):
        """
        Set the time-focus calibration to reduction manager.
        :param focus_cal_file:
        :return:
        """
        self._reductionManager.set_focus_calibration_file(focus_cal_file)

        return

    def set_reduction_flag(self, run_number, flag):
        """ Set the  reduction flag for a file in SAMPLE run dictionary of this project
        Requirements: run number is non-negative integer and flag is boolean.
        Guarantees:
        :param run_number:
        :param flag: reduction flag
        :return:
        """
        # Check requirements
        assert isinstance(run_number, int)
        assert isinstance(flag, bool)
        assert run_number in self._dataFileDict, 'Run %d is not scanned. Current scanned runs are %s.' % (
            run_number, str(self._dataFileDict.keys()))

        # Check with full name
        file_name = self._dataFileDict[run_number][0]
        assert os.path.exists(file_name), 'Unable to find data file %s.' % file_name

        # Set value
        self._sampleRunReductionFlagDict[run_number] = flag

        return

    def set_reduction_parameters(self, parameter_dict):
        """
        Purpose: set up the parameters to reduce run
        Requirements:
        - reduction manager is available
        - input is a dictionary, key=parameter name, value=parameter value
        :param parameter_dict:
        :return:
        """
        # Check requirements
        assert self._reductionManager is not None
        assert isinstance(parameter_dict, dict)

        self._reductionManager.set_parameters(parameter_dict)

        return

    def set_base_data_path(self, data_dir):
        """ Set base data path such as /SNS/VULCAN/
        to locate the data via run number and IPTS
        Requirements:
        1. input is an existing file directory
        :param data_dir: base data directory. for example, /SNS/VULCAN/
        :return: None
        """
        if isinstance(data_dir, str) is True:
            assert os.path.exists(data_dir)
            self._baseDataPath = data_dir
        else:
            raise OSError("Unable to set base data path with unsupported format %s." % str(type(data_dir)))

        return

    def slice_data(self, run_number, splitter_ws_name, info_ws_name, out_base_name):
        """
        Split data by event filter
        :param run_number:
        :param splitter_ws_name:
        :param info_ws_name:
        :param out_base_name:
        :return: 2-tuple (boolean, object): True/(list of ws names, list of ws objects); False/error message
        """
        # Load data to event workspace
        ret_obj = self.get_run_info(run_number)
        nxs_file_name = ret_obj[0]
        event_ws_name = mantid_helper.event_data_ws_name(run_number)
        mantid_helper.load_nexus(data_file_name=nxs_file_name, output_ws_name=event_ws_name, meta_data_only=False)

        # Split
        splitted_ws_base_name = mantid_helper.get_split_workpsace_base_name(run_number, out_base_name)
        status, ret_obj = mantid_helper.split_event_data(event_ws_name, splitter_ws_name, info_ws_name,
                                                         splitted_ws_base_name, tof_correction=False)

        if status is True:
            self._clear_split_run(run_number)
            self._splitWorkspaceDict[run_number] = ret_obj[1]

        return status, ret_obj[0]

    def _generateFileName(self, runnumber, iptsstr):
        """ Generate a NeXus file name with full path with essential information

        Arguments:
         - runnumber :: integer run number
         - iptsstr   :: string for IPTS.  It can be either an integer or in format as IPTS-####. 
        """
        # Parse run number and IPTS number
        run = int(runnumber)
        iptsstr = str(iptsstr).lower().split('ipts-')[-1]
        ipts = int(iptsstr)

        # Build file name with path
        # FIXME : VULCAN only now!
        nxsfname = os.path.join(self._baseDataPath, 'IPTS-%d/0/%d/NeXus/VULCAN_%d_event.nxs'%(ipts, run, run))
        if os.path.exists(nxsfname) is False:
            print "[Warning] NeXus file %s does not exist.  Check run number and IPTS." % (nxsfname)
        else:
            print "[DB] Successfully generate an existing NeXus file with name %s." % (nxsfname)

        return nxsfname

        
class DeprecatedReductionProject(VDProject):
    """ Class to handle reducing powder diffraction data
    :Note: it is deprecated!
    """ 

    def __init__(self, project_name):
        """
        """
        VDProject.__init__(self, project_name)
        
        # detector calibration/focusing file
        self._detCalFilename = None
        # calibration file dictionary: key = base data file name, value = (cal file list, index)
        self._datacalibfiledict = {}
        # calibration file to run look up table: key = calibration file with fullpath. value = list
        self._calibfiledatadict = {}
        # vanadium record (database) file
        self._vanadiumRecordFile = None
        # flags to reduce specific data set: key = file with full path
        self._reductionFlagDict = {} 
        # dictionary to map vanadium run with IPTS. key: integer  
        self._myVanRunIptsDict = {}

        # Reduction status
        self._lastReductionSuccess = None

        # Reduction result dictionary
        self._myRunPdrDict = {}
        
        self._tofMin = None
        self._tofMax = None

        return
        
    def addData(self, datafilename):
        """ Add a new data file to project
        """
        raise NotImplementedError("addData is private")

    def addDataFileSets(self, reddatasets):
        """ Add data file and calibration file sets 
        """
        for datafile, vcalfilelist in reddatasets:
            # data file list
            self._dataFileDict.append(datafile)
            # data file and set default to 0th element
            databasefname = os.path.basename(datafile)
            self._baseDataFileNameList.append(databasefname)
            self._datacalibfiledict[databasefname] = (vcalfilelist, 0)


            # FIXME : This will be moved to a stage that is just before reduction
            # van cal /data file dict
            # print "_calibfiledatadict: ", type(self._calibfiledatadict)
            # print "key: ", vcalfile

            # raise NotImplementedError("Need to determine the calibration file first!")
            # if self._calibfiledatadict.has_key(vcalfile) is False:
            #     self._calibfiledatadict[vcalfile] = []
            # # self._calibfiledatadict[vcalfile].append(datafile)
        # ENDFOR
        
        return

    def addVanadiumIPTSInfo(self, vaniptsdict):
        """ Add vanadium's IPTS information for future locating NeXus file
        """
        for vanrun in vaniptsdict.keys():
            self._myVanRunIptsDict[int(vanrun)] = vaniptsdict[vanrun]

        return


    def deleteData(self, datafilename):
        """ Delete a data: override base class
        Arguments: 
         - datafilename :: data file name with full path
        """
        # FIXME - A better file indexing data structure should be used
        # search data file list
        if datafilename not in self._dataFileDict:
            # a base file name is used
            for dfname in self._dataFileDict:
                basename = os.path.basename(dfname)
                if basename == datafilename:
                    datafilename = dfname
                    break
            # END(for)
        # ENDIF

        if datafilename not in self._dataFileDict:
            return (False, "data file %s is not in the project" % (datafilename))

        # remove from dataset
        self._dataFileDict.remove(datafilename)
        # remove from data file/van cal dict
        basename = os.path.basename(datafilename)
        vanfilename = self._datacalibfiledict.pop(basename)
        # remove from van cal/data file dict
        # FIXME - _calibfiledatadict will be set up only before reduction
        # self._calibfiledatadict.pop(vanfilename)

        return True, ""

    def getDataFilePairs(self):
        """ Get to know 
        """
        pairlist = []
        for datafile in self._datacalibfiledict.keys():
            pairlist.append( (datafile, self._datacalibfiledict[datafile]) )

        return pairlist

    def getTempSmoothedVanadium(self, run):
        """
        """
        runbasename = os.path.basename(run)
        
        returndict = None
        if self._myRunPdrDict.has_key(runbasename):
            runpdr = self._myRunPdrDict[runbasename]
            ws = runpdr.get_smoothed_vanadium()
            
            if ws is not None:
                ws = ConvertToPointData(InputWorkspace=ws)

                returndict = {}
                for iws in xrange(ws.getNumberHistograms()):
                    vecx = ws.readX(iws)[:]
                    vecy = ws.readY(iws)[:]
                    returndict[iws] = (vecx, vecy)
                # ENDFOR
            # ENDIF
        # ENDIF
        
        return returndict

    def getVanadiumRecordFile(self):
        """
        """
        return self._vanadiumRecordFile

    def info(self):
        """ Return information in nice format
        """
        ibuf = "%-50s \t%-30s\t %-5s\n" % ("File name", "Vanadium run", "Reduce?")
        for filename in self._dataFileDict:
            basename = os.path.basename(filename)
            vanrun = self._datacalibfiledict[basename]
            try: 
                reduceBool = self._reductionFlagDict[filename]
            except KeyError as e:
                # print "Existing keys for self._reductionFlagDict are : %s." % (
                #         str(sorted(self._reductionFlagDict.keys())))
                ibuf += "%-50s \tUnable to reduce!\n" % (filename)
            else: 
                ibuf += "%-50s \t%-30s\t %-5s\n" % (filename, str(vanrun), str(reduceBool))
        # ENDFOR

        return ibuf

    def hasData(self, datafilename):
        """ Check whether project has such data file 
        """
        # Check data set with full name
        if self._dataFileDict.count(datafilename) == 1:
            return True


    def isSuccessful(self):
        """ Check whether last reduction is successful

        Return :: boolean
        """
        return self._lastReductionSuccess
        
        
    def setCalibrationFile(self, datafilenames, calibfilename):
        """ Set the vanadium calibration file to a set of data file in the 
        project
        Arguments:
         - datafilenames :: list of data file with full path
        """
        # FIXME - Rename to setVanCalFile
        errmsg = ""
        numfails = 0

        for datafilename in datafilenames:
            # check whether they exist in the project
            if datafilename not in self._dataFileDict:
                errmsg += "Data file %s does not exist.\n" % (datafilename)
                numfails += 1
                continue

            # get base name
            basefilename = os.path.basename(datafilenames)
            # data file/calib dict 
            self._datacalibfiledict[basefilename] = calibfilename
           
            # calib / data file dict
            if self._calibfiledatadict.has_key(calibfilename) is False:
                self._calibfiledatadict[calibfilename] = []
            self._calibfiledatadict[calibfilename].append(datafilename)
        # ENDFOR(datafilename)

        if numfails == len(datafilenames):
            r = False
        else:
            r = True
    
        return (r, errmsg)

    def setCharacterFile(self, characerfilename):
        """ Set characterization file
        """
        self._characterfilename = characerfilename
        
        
    def setDetCalFile(self, detcalfilename):
        """ Set detector calibration file for focussing data
        """
        self._detCalFilename = detcalfilename
        if os.path.exists(self._detCalFilename) is False:
            return False
        
        return True        
        

    def setFilter(self):
        """ Set events filter for chopping the data
        """

        return

    def setParameters(self, paramdict):
        """ Set parameters in addition to those necessary
        """
        if isinstance(paramdict, dict) is False:
            raise NotImplementedError("setParameters is supposed to get a dictionary")
            
        self._paramDict = paramdict
        
        return

    def setTOFRange(self, tofmin, tofmax):
        """ set range of TOF
        """
        self._tofMin = tofmin
        self._tofMax = tofmax

        return

    def setVanadiumDatabaseFile(self, datafilename):
        """ Set the vanadium data base file
        """
        self._vanadiumRecordFile = datafilename

        return
        
    def stripVanadiumPeaks(self, datafilename): 
        """ Strip vanadium peaks from a reduced run
        """
        basefname = os.path.basename(datafilename)
        reductmanager = self._myRunPdrDict[basefname]

        status, errmsg = reductmanager.stripVanadiumPeaks()

        return status, errmsg