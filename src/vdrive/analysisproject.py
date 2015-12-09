__author__ = 'wzz'


class AnalysisProject:
    """ VDrive Analysis Project
    """
    def __init__(self):
        """ Initialization
        """

        return


    def getData(self, basedatafilename):
        """ Get data X, Y and E
        """
        # get file name
        fullpathdatafname = self._getFullpathFileName(basedatafilename)
        if fullpathdatafname is None:
            return (False, "Data file name %s does not exist in project. " % (basedatafilename))

        if os.path.exists(fullpathdatafname):
            return (False, "Data file name %s cannot be found. " % (fullpathdatafname))

        # retrieve
        ws = mantid.LoadGSS(Filename=fullpathdatafname)

        # FIXME - Consider single-spectrum GSS file only!

        return (True, [ws.readX(0), ws.readY(0), ws.readE(0)])

