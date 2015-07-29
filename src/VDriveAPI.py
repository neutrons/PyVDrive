#####
# Ui_VDrive (beta)
#####
import vdrive.VDProject as vp
import vdrive.mantid_helper as mtd

class VDriveAPI(object):
    """

    """
    def __init__(self):
        """

        :return:
        """
        self._instrumentName = 'VULCAN'

        self._myProject = vp.VDProject('Temp')

        self._tempWSDict = {}

        return


    def add_runs(self, iptsdir):
        """

        :param iptsdir:
        :return:
        """
        # FIXME - Copy from UI_VDrive

        raise NotImplementedError('ASAP')


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

