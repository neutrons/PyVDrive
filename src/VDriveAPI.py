#####
# Ui_VDrive (beta)
#
# boundary between VDProject and API
# 1. API accepts root directory, runs and etc
# 2. VDProject accepts file names with full path
#
#####
import os

import vdrive.VDProject as vp
import vdrive.mantid_helper as mtd
import vdrive.FacilityUtil as futil

class VDriveAPI(object):
    """

    """
    def __init__(self):
        """

        :return:
        """
        # Define class variables with defaults
        self._instrumentName = 'VULCAN'
        self._myRootDataDir = '/SNS/VULCAN'
        self._myWorkDir = '/tmp/'

        self._currentIPTS = -1

        # Project
        self._myProject = vp.VDProject('Temp')
        self._myFacilityHelper = futil.FacilityUtilityHelper(self._instrumentName)

        #self._tempWSDict = {}

        return

    def add_runs(self, ipts_dir):
        """
        Add runs under an IPTS dir to project
        :param ipts_dir:
        :return:
        """
        return

    def clear_runs(self):
        """

        :return:
        """
        self._myProject.clear_runs()

        return

    def filter_runs_by_date(self, run_tuple_list, start_date, end_date):
        """
        Filter runs by date.  Any runs ON and AFTER start_date and BEFORE end_date
        will be included.
        :param run_tuple_list: 3-tuple: run number, epoch time in second, file name with full path
        :param start_date:
        :param end_date:
        :return:
        """
        # Get starting date and end date's epoch time
        try:
            epoch_start = futil.convert_to_epoch(start_date)
            epoch_end = futil.convert_to_epoch(end_date)
            print '[DB] Time range: %f, %f with dT = %f hours' % (epoch_start, epoch_end,
                                                                  (epoch_end-epoch_start)/3600.)
        except ValueError as e:
            return False, str(e)

        # Sort by time
        assert isinstance(run_tuple_list, list)
        run_tuple_list.sort(key=lambda x: x[1])
        print '[DB] Runs range from (epoch time) %f to %f' % (run_tuple_list[0][1],
                                                              run_tuple_list[-1][1])

        # FIXME - Using binary search will be great!
        result_list = []
        for tup in run_tuple_list:
            file_epoch = tup[1]
            if epoch_start <= file_epoch < epoch_end:
                result_list.append(tup[:])
            # END-IF
        # END-IF

        print '[DB] Return!!!'

        return True, result_list


    def loadNexus(self, filename, logonly):
        """

        :param filename:
        :param logonly:
        :return:
        """
        out_ws_name = 'templogws'
        status, errmsg, value = mtd.loadNexus(datafilename=filename,
                                              outwsname=out_ws_name,
                                              metadataonly=logonly)
        if status is False:
            return False, errmsg, None

        tag = out_ws_name
        logws = value
        self._tempWSDict[tag] = logws

        return True, '', tag

    def get_ipts_info(self, ipts_number):
        """

        :param ipts_number:
        :return:
        """
        # TODO - DOC
        try:
            run_tuple_list = self._myFacilityHelper.get_run_info(ipts_number)
        except RuntimeError as e:
            return False, str(e)

        return True, run_tuple_list

    def getSampleLogNames(self, tag):
        """
        :param tag:
        :return:
        """
        if self._tempWSDict.has_key(tag) is False:
            return False, 'Tag %s cannot be found in temporary workspace dictionary'%(tag), None

        logws = self._tempWSDict[tag]
        plist = logws.getRun().getProperties()
        print len(plist)
        pnamelist = []
        for p in plist:
            try:
                if p.size() > 1:
                    pnamelist.append(p.name)
            except AttributeError:
                pass

        return True, '', pnamelist

    def getSampleLogVectorByIndex(self, tag, logindex):
        """

        :param tag:
        :param logindex:
        :return:
        """
        # Get log value
        logname = str(self.ui.comboBox_2.currentText())
        if len(logname) == 0:
            # return due to the empty one is chozen
            return

        samplelog = self._dataWS.getRun().getProperty(logname)
        vectimes = samplelog.times
        vecvalue = samplelog.value

        # check
        if len(vectimes) == 0:
            print "Empty log!"

        # Convert absolute time to relative time in seconds
        t0 = self._dataWS.getRun().getProperty("proton_charge").times[0]
        t0ns = t0.totalNanoseconds()

        # append 1 more log if original log only has 1 value
        tf = self._dataWS.getRun().getProperty("proton_charge").times[-1]
        vectimes.append(tf)
        vecvalue = numpy.append(vecvalue, vecvalue[-1])

        vecreltimes = []
        for t in vectimes:
            rt = float(t.totalNanoseconds() - t0ns) * 1.0E-9
            vecreltimes.append(rt)


    def set_data_root_directory(self, root_dir):
        """
        :rtype : tuple
        :param root_dir:
        :return:
        """
        # TODO - Doc
        # Check existence
        if os.path.exists(root_dir) is False:
            return False, 'Directory %s cannot be found.' % (root_dir)

        self._myRootDataDir = root_dir
        self._myFacilityHelper.set_data_root_path(self._myRootDataDir)

        return True, ''

    def set_ipts(self, ipts_number):
        """

        :return:
        """
        # TODO - Doc
        try:
            self._currentIPTS = int(ipts_number)
        except ValueError as e:
            return False, 'Unable to set IPTS number due to %s.' % str(e)

        return True, ''


    def set_working_directory(self, work_dir):
        """

        :param work_dir:
        :return:
        """
        # TODO - Doc
        # TODO - Create directory if it does not exist

        # Check writable
        if os.access(work_dir, os.W_OK) is False:
            return False, 'Working directory %s is not writable.' % (work_dir)
        else:
            self._myWorkDir = work_dir

        return True, ''


