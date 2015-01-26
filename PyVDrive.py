################################################################################
# UI class for project Py-VDrive
# - A GUI application will call this class for data reduction and analysis;
# - User can write script on this class to reduce and analyze data;
################################################################################

class PyVDrive:
    """ Class PyVDrive
    """
    def __init__(self):
        """ Init
        """
        self._projectDict = {}
        self._name = ""
        
        return
        
        
    def newProject(self, projname):
        """ Add a new project
        """ 
        self._name = projname
        
        return False
        
        
    def loadProject(self, projfilename):
        """ Load an existing project
        """
        raise NotImplementedError("Implement ASAP")
        
        
        return False