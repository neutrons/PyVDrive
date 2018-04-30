# Set up the testing environment for PyVDrive commands
from pyvdrive.interface import vcommand_processor
from pyvdrive.interface.VDrivePlot import VdriveMainWindow


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
