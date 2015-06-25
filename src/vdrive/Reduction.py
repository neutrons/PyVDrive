##########
#
# Methods refactored from SNSPowderReduction for better flexibility to merged into PyVDrive
#
##########

def focus(self, nxsfilename, calib, filterWall, splitwksp=None, preserveEvents=True):
    """ Load, (optional) split and focus data in chunks
    Arguments:
        - nxsfilename :: file name for raw NeXus data file
        - splitwksp: SplittersWorkspace (if None then no split)
        - filterWall: 2-tuple for t_min and t_max
    Return:
    """
    # generate the workspace name
    self.log().information("_focusChunks(): runnumber = %d, extension = %s" % (runnumber, extension))
    dosplit = False
    
    # determine number of workspaces
    numwksp = 1
    if splitwksp is not None:
        # Check consistency in the code
        if filterWall[0] < 1.0E-20 and filterWall[1] < 1.0E-20:
            # Default definition of filterWall when there is no split workspace specified.
            raise NotImplementedError("It is impossible to have a not-NONE splitters workspace and (0,0) time filter wall.")
        # ENDIF
        
        # FIXME Unfiltered workspace (remainder) is not considered here
        numwksp = self.getNumberOfSplittedWorkspace(splitwksp)
        numsplitters = splitwksp.rowCount()
    # ENDIF (splitwksp)

    # Do explicit FilterEvents if number of splitters is larger than 1.
    # If number of splitters is equal to 1, then filterWall will do the job itself.
    if numsplitters > 1:
        dosplit = True
        self.log().debug("[Fx948] Number of split workspaces = %d; Do split = %s" % (numwksp, str(dosplit)))
    # ENDIF

    # Create a list for splitted workspaces
    wksplist = []
    for n in xrange(numwksp):
        # In some cases, there will be 1 more splitted workspace (unfiltered)
        wksplist.append(None)
        self.log().debug("F1141A: Number of workspace to process = %d" %(numwksp))


    # Filter events if possible
    if temp.id() == EVENT_WORKSPACE_ID and dosplit is True:

        # Splitting workspace
        basename = str(temp)
        if self._splitinfotablews is None:
            api.FilterEvents(InputWorkspace=temp, OutputWorkspaceBaseName=basename,\
                SplitterWorkspace=splitwksp, \
                GroupWorkspaces=True)
        else:
            api.FilterEvents(InputWorkspace=temp, OutputWorkspaceBaseName=basename,\
                SplitterWorkspace=splitwksp, InformationWorkspace = str(self._splitinfotablews),\
                GroupWorkspaces=True)
        # ENDIF(existing split information workspace)
        
        wsgroup = mtd[basename]
        
        if DBOUTPUT is True:
            tempwsnamelist = wsgroup.getNames()
            dbstr = "[Fx951] Splitted workspace names: "
            for wsname in tempwsnamelist:
                dbstr += "%s, " % (wsname)
            self.log().debug(dbstr)
            
        # create a workspace list
        tempwslist = []
        for wsname in tempwsnamelist:
            tempws = mtd[wsname]
            if tempws is not None: 
                # keep non-remainder workspaces and delete 'unfiltered'/remainder
                if wsname.endswith("_unfiltered") is False:
                    tempwslist.append(tempws) 
                else: 
                    api.DeleteWorkspace(Workspace=tempws)
                #ENDIF(wsname)
            #ENDIF(tempws) 
        # ENDFOR(wsname) 
    
    else:
        # Histogram data i.e, non-event workspace or event workspace won't be split
        tempwslist.append(temp) 

    # ENDIF(temp.id and dosplit) 
    
    # Update number of workspaces 
    numwksp = len(tempwslist)

    if DBOUTPUT is True:
        msg = "[Fx1142] Workspace of chunk %d is %d/%d. \n" % (ichunk, len(tempwslist), numwksp)
        for iws in xrange(len(tempwslist)):
            ws = tempwslist[iws]
            msg += "%s\t\t" % (str(ws))
            if iws %5 == 4:
                msg += "\n"
        self.log().debug(msg)

    # Align and focus for all workspaces
    for itemp in xrange(numwksp): 
        temp = tempwslist[itemp] 
        
        # align and focus 
        focuspos = self._focusPos
        temp = api.AlignAndFocusPowder(InputWorkspace=temp, OutputWorkspace=temp, 
                CalFileName=calib, Params=self._binning, Dspacing=self._bin_in_dspace, \
                DMin=self._info["d_min"], DMax=self._info["d_max"], \
                TMin=self._info["tof_min"], TMax=self._info["tof_max"], \
                PreserveEvents=preserveEvents, \
                RemovePromptPulseWidth=self._removePromptPulseWidth, CompressTolerance=COMPRESS_TOL_TOF, \
                UnwrapRef=self._LRef, LowResRef=self._DIFCref, LowResSpectrumOffset=self._lowResTOFoffset, \
                CropWavelengthMin=self._wavelengthMin, **(focuspos))

        if DEBUGOUTPUT is True:
            for iws in xrange(temp.getNumberHistograms()):
                spec = temp.getSpectrum(iws)
                self.log().debug("[DBx131] ws %d: spectrum ID = %d. " % (iws, spec.getSpectrumNo()))
                
            if preserveEvents is True and isinstance(temp, mantid.api._api.IEventWorkspace) is True:
                self.log().information("After being aligned and focussed workspace %s; Number of events = %d \
                    of chunk %d " % (str(temp),temp.getNumberEvents(), ichunk))
    
            
        # Rename and/or add to workspace of same splitter but different chunk
        wkspname = wksp
        if numwksp > 1:
            wkspname += "_%s" % ( (str(temp)).split("_")[-1] )
        wksplist[itemp] = api.RenameWorkspace(InputWorkspace=temp, OutputWorkspace=wkspname)
    # ENDFOR (itemp)
    
    
    
def setupGSASIParmFileName(wksplist, iparmfilename):
    """ Set up GSAS instrument parameter names
    """
    for itemp in xrange(numwksp): 
        wksplist[itemp].getRun()['iparm_file'] = iparmfilename 
    
    return
    
def compressEvents(wksplist):
    """ Compress events
    """
    for itemp in xrange(numwksp): 
        if wksplist[itemp].id() == EVENT_WORKSPACE_ID: 
            wksplist[itemp] = api.CompressEvents(InputWorkspace=wksplist[itemp],\
                OutputWorkspace=wksplist[itemp], Tolerance=COMPRESS_TOL_TOF) # 100ns
                
def normalizeByCurrent(wksplist):
    """ normalize by current
    """
    for itemp in xrange(len(wksplist)):
        wksplist[itemp] = api.NormaliseByCurrent(InputWorkspace=wksplist[itemp],\
            OutputWorkspace=wksplist[itemp])
        wksplist[itemp].getRun()['gsas_monitor'] = 1
    # ENDFOR
    
    return
    
    
def exportForAnalysis(wksplist, filetypelist):
    """
    """
    for itemp in xrange(len(wksplist)):
        _save(wksplist[itemp], filetypelist)

    return
