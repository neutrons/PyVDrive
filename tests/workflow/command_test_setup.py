# Set up the testing environment for PyVDrive commands
import os
import sys
from pyvdrive.interface import vcommand_processor
from pyvdrive.interface.VDrivePlot import VdriveMainWindow
home_dir = os.path.expanduser('~')
# NOTE: This is the entry point to define the path to Mantid
if home_dir.startswith('/SNS/'):
    # analysis
    sys.path.insert(1, '/opt/mantidnightly/bin/')
elif home_dir.startswith('/home/wzz') is False:
    # Mac debug build
    sys.path.append('/Users/wzz/MantidBuild/debug-stable/bin')
    # Analysis cluster build
    # No need: auto set sys.path.append('/opt/mantidnightly/bin/')
    sys.path.insert(1, '/SNS/users/wzz/Mantid_Project/builds/debug/bin')
    # print ('system path: {0}'.format(sys.path))
    # Personal VULCAN build
    sys.path.append('/SNS/users/wzz/Mantid_Project/builds/build-vulcan/bin')
    # sys.path.append('/SNS/users/wzz/Mantid_Project/builds/build-vulcan/bin')


class PyVdriveCommandTestEnvironment(object):
    """
    PyVDrive commands testing environment
    """
    def __init__(self):
        """
        initialization
        """
        self._main_window = VdriveMainWindow(None)

        self._command_history = list()

        # create main application
        self._command_process = vcommand_processor.VdriveCommandProcessor(self._main_window,
                                                                          self._main_window.get_controller())

        return

    @property
    def main_window(self):
        return self._main_window

    def run_command(self, vdrive_command):
        """
        execute a command
        :param vdrive_command:
        :return:
        """

        print ('Run {0}'.format(vdrive_command))
        self._main_window.execute_command(vdrive_command)
