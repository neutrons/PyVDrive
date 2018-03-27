# script to do cross-correlation
import os
from mantid.kernel import AnalysisDataService as mtd
from mantid.simpleapi import CrossCorrelate, GetDetectorOffsets, SaveCalFile, ConvertDiffCal, SaveDiffCal
from mantid.simpleapi import RenameWorspace, Plus


def cc_calibrate(ws_name, peak_position, peak_min, peak_max, ws_index_range, reference_ws_index, cc_number, max_offset,
                 binning, index=''):
    """
    cross correlation calibration on a
    :param ws_name:
    :param peak_position:
    :param peak_min:
    :param peak_max:
    :param ws_index_range:
    :param reference_ws_index:
    :param cc_number:
    :param max_offset:
    :param binning:
    :param index:
    :return:
    """
    workspace = mtd[ws_name]

    # find reference workspace
    if reference_ws_index is None:
        # Find good peak for reference: strongest???
        ymax = 0
        for s in range(0, workspace.getNumberHistograms()):
            y_s = workspace.readY(s)
            midBin = int(workspace.blocksize() / 2)
            if y_s[midBin] > ymax:
                reference_ws_index = s
                ymax = y_s[midBin]
    # END-IF
    print ('Reference spectra=%s' % reference_ws_index)

    # Cross correlate spectra using interval around peak at peakpos (d-Spacing)
    CrossCorrelate(InputWorkspace=ws_name,
                   OutputWorkspace=ws_name+"cc"+index,
                   ReferenceSpectra=reference_ws_index,
                   WorkspaceIndexMin=ws_index_range[0], WorkspaceIndexMax=ws_index_range[1],
                   XMin=peak_min, XMax=peak_max)

    # Get offsets for pixels using interval around cross correlations center and peak at peakpos (d-Spacing)
    offset_ws_name = ws_name+"offset"+index
    mask_ws_name = ws_name+"mask"+index
    GetDetectorOffsets(InputWorkspace=ws_name+"cc"+index,
                       OutputWorkspace=offset_ws_name, MaskWorkspace=mask_ws_name,
                       Step=abs(binning),
                       DReference=peak_position,
                       XMin=-cc_number, XMax=cc_number,
                       MaxOffset=max_offset)

    # check result and remove interval result
    if mtd.doesExist(ws_name+"cc"):
        mtd.remove(ws_name+"cc")

    return offset_ws_name, mask_ws_name


def save_calibration(ws_name, offset_mask_list, group_ws_name, calib_file_prefix):
    """

    :param ws_name:
    :param offset_mask_list:
    :param group_ws_name:
    :param calib_file_prefix:
    :return:
    """
    # combine the offset and mask workspaces
    offset_ws_name0, mask_ws_name0 = offset_mask_list[0]
    offset_ws_name = ws_name + '_offset'
    mask_ws_name = ws_name + '_mask'
    if offset_ws_name != offset_ws_name0:
        RenameWorspace(InputWorkspace=offset_ws_name0, OutputWorkspace=offset_ws_name)
    if mask_ws_name != mask_ws_name0:
        RenameWorspace(InputWorkspace=mask_ws_name0, OutputWorkspace=mask_ws_name)

    for ituple in range(1, len(offset_mask_list)):
        offset_ws_name_i, mask_ws_name_i = offset_mask_list[ituple]
        Plus(LHSWorkspace=offset_ws_name, RHSWorkspace=offset_ws_name_i,
             OutputWorkspace=offset_ws_name)
        Plus(LHSWorkspace=mask_ws_name, RHSWorkspace=mask_ws_name_i,
             OutputWorkspace=mask_ws_name)

    # for the sake of legacy
    SaveCalFile(OffsetsWorkspace=offset_ws_name,
                GroupingWorkspace=group_ws_name,
                MaskWorkspace=wkspName+"mask",
                Filename=os.path.join(os.getcwd(), calib_file_prefix + '.cal'))

    # the real version
    out_file_name = os.path.join(os.getcwd(), calib_file_prefix + '.h5')
    if os.path.exists(out_file_name):
        os.unlink(out_file_name)
    calib_ws_name = ws_name+'_cal'
    ConvertDiffCal(OffsetsWorkspace=offset_ws_name,
                   OutputWorkspace=calib_ws_name)
    SaveDiffCal(CalibrationWorkspace=calib_ws_name,
                GroupingWorkspace=group_ws_name,
                MaskWorkspace=mask_ws_name,
                Filename=out_file_name)

    print ('Calibration file is saved as {0}'.format(out_file_name))

    return calib_ws_name, offset_ws_name, mask_ws_name


def cross_correlate_vulcan_data(group_ws_name):
    wkspName = 'full_diamond'
    peakpos1 = 1.2614
    peakpos2 = 1.2614
    peakpos3 = 1.07577

    ref_ws_index = 1613
    west_offset, west_mask = cc_calibrate(wkspName, peakpos1, peakpos1-0.01, peakpos1+0.01, [0, 3234],
                                          ref_ws_index, 100, 1, -0.0003, 'west')

    ref_ws_index = 4847
    east_offset, east_mask = cc_calibrate(wkspName, peakpos2, peakpos2-0.01, peakpos2+0.01, [3234, 6468],
                                          ref_ws_index, 100, 1, -0.0003, 'east')

    save_calibration(wkspName, [(west_offset, west_mask), (east_offset, east_mask)], group_ws_name, 'vulcan_vz_test')

    return



def cccalibrate(wksp, peakpos1, peakpos2, peakpos3,  lastpixel=0, ccnumber=100, maxoffset=1):
    if wksp is None:
        return None

    # Bin events in d-Spacing
    # Rebin(InputWorkspace=wksp, OutputWorkspace=wksp,
    #       Params=str(self._peakmin)+","+str(abs(self._binning[1]))+","+str(self._peakmax))

    #Find good peak for reference: strongest???
    ymax = 0
    for s in range(0,mtd[wksp].getNumberHistograms()):
        y_s = mtd[wksp].readY(s)
        midBin = int(mtd[wksp].blocksize()/2)
        if y_s[midBin] > ymax:
            refpixel = s
            ymax = y_s[midBin]
    # self.log().information("Reference spectra=%s" % refpixel)
    print ('Reference spectra=%s' % refpixel)

    # Cross correlate spectra using interval around peak at peakpos (d-Spacing)

    if lastpixel == 0:
        lastpixel = mtd[wksp].getNumberHistograms()-1
    else:
        lastpixel = int(mtd[wksp].getNumberHistograms()*lastpixel/self._lastpixel3) - 1
    print ("Last pixel=%s" % lastpixel)
    CrossCorrelate(InputWorkspace=wksp, OutputWorkspace=wksp+"cc",
                   ReferenceSpectra=refpixel, WorkspaceIndexMin=0,
                   WorkspaceIndexMax=lastpixel,
                   XMin=peakpos1 - 0.01, XMax=peakpos1 + 0.01)
    # Get offsets for pixels using interval around cross correlations center and peak at peakpos (d-Spacing)
    GetDetectorOffsets(InputWorkspace=wksp+"cc", OutputWorkspace=wksp+"offset",
                       Step=0.0003, DReference=peakpos1,
                       XMin=-ccnumber, XMax=ccnumber,
                       MaxOffset=maxoffset, MaskWorkspace=wksp+"mask")
    if AnalysisDataService.doesExist(wksp+"cc"):
        AnalysisDataService.remove(wksp+"cc")
    if peakpos2 > 0.0:
        Rebin(InputWorkspace=wksp, OutputWorkspace=wksp,
              Params=str(self._peakmin2)+","+str(abs(self._binning[1]))+","+str(self._peakmax2))
        #Find good peak for reference
        ymax = 0
        for s in range(0,mtd[wksp].getNumberHistograms()):
            y_s = mtd[wksp].readY(s)
            midBin = int(mtd[wksp].blocksize()/2)
            if y_s[midBin] > ymax:
                refpixel = s
                ymax = y_s[midBin]
        msg = "Reference spectra = %s, lastpixel_3 = %s" % (refpixel, self._lastpixel3)
        self.log().information(msg)
        self._lastpixel2 = int(mtd[wksp].getNumberHistograms()*self._lastpixel2/self._lastpixel3) - 1
        CrossCorrelate(InputWorkspace=wksp, OutputWorkspace=wksp+"cc2",
                       ReferenceSpectra=refpixel, WorkspaceIndexMin=self._lastpixel+1,
                       WorkspaceIndexMax=self._lastpixel2,
                       XMin=self._peakmin2, XMax=self._peakmax2)
        # Get offsets for pixels using interval around cross correlations center and peak at peakpos (d-Spacing)
        GetDetectorOffsets(InputWorkspace=wksp+"cc2", OutputWorkspace=wksp+"offset2",
                           Step=abs(self._binning[1]), DReference=self._peakpos2,
                           XMin=ccnumber, XMax=ccnumber,
                           MaxOffset=self._maxoffset, MaskWorkspace=wksp+"mask2")
        Plus(LHSWorkspace=wksp+"offset", RHSWorkspace=wksp+"offset2",
             OutputWorkspace=wksp+"offset")
        Plus(LHSWorkspace=wksp+"mask", RHSWorkspace=wksp+"mask2",
             OutputWorkspace=wksp+"mask")
        for ws in [wksp+"cc2", wksp+"offset2", wksp+"mask2"]:
            if AnalysisDataService.doesExist(ws):
                AnalysisDataService.remove(ws)

    if peakpos3 > 0.0:
        Rebin(InputWorkspace=wksp, OutputWorkspace=wksp,
              Params=str(self._peakmin3)+","+str(abs(self._binning[1]))+","+str(self._peakmax3))
        #Find good peak for reference
        ymax = 0
        for s in range(0,mtd[wksp].getNumberHistograms()):
            y_s = mtd[wksp].readY(s)
            midBin = mtd[wksp].blocksize()/2
            if y_s[midBin] > ymax:
                refpixel = s
                ymax = y_s[midBin]
        self.log().information("Reference spectra=%s" % refpixel)
        CrossCorrelate(InputWorkspace=wksp, OutputWorkspace=wksp+"cc3",
                       ReferenceSpectra=refpixel,
                       WorkspaceIndexMin=self._lastpixel2+1,
                       WorkspaceIndexMax=mtd[wksp].getNumberHistograms()-1,
                       XMin=self._peakmin3, XMax=self._peakmax3)
        # Get offsets for pixels using interval around cross correlations center and peak at peakpos (d-Spacing)
        GetDetectorOffsets(InputWorkspace=wksp+"cc3", OutputWorkspace=wksp+"offset3",
                           Step=abs(self._binning[1]), DReference=self._peakpos3,
                           XMin=-self._ccnumber, XMax=self._ccnumber,
                           MaxOffset=self._maxoffset, MaskWorkspace=wksp+"mask3")
        Plus(LHSWorkspace=wksp+"offset", RHSWorkspace=wksp+"offset3",
             OutputWorkspace=str(wksp)+"offset")
        Plus(LHSWorkspace=wksp+"mask", RHSWorkspace=wksp+"mask3",
             OutputWorkspace=wksp+"mask")
        for ws in [wksp+"cc3", wksp+"offset3", wksp+"mask3"]:
            if AnalysisDataService.doesExist(ws):
                AnalysisDataService.remove(ws)

    return str(wksp)


def saveCalibration(wkspName, calibFilePrefix):
    outfilename = None

    # for the sake of legacy
    SaveCalFile(OffsetsWorkspace=wkspName+"offset",
                #GroupingWorkspace=wkspName+"group",
                MaskWorkspace=wkspName+"mask",Filename=calibFilePrefix + '.cal')
    # the real version
    outfilename = calibFilePrefix + '.h5'
    if os.path.exists(outfilename):
        os.unlink(outfilename)
    ConvertDiffCal(OffsetsWorkspace=wkspName+"offset",
                   OutputWorkspace=wkspName+"cal")
    SaveDiffCal(CalibrationWorkspace=wkspName+"cal",
                #GroupingWorkspace=wkspName+"group",
                MaskWorkspace=wkspName+"mask",
                Filename=outfilename)

    return

# wkspName ='full_diamon'
# peakpos1 = 1.2614
# peakpos2 = 1.2614
# peakpos3 = 1.07577
# cal_ws_name = cccalibrate(wkspName, peakpos1, peakpos2, peakpos3)
# print ('Returned workspace: {0}'.format(cal_ws_name))
# saveCalibration(wkspName, calibFilePrefix='VulcanWestTemp')
