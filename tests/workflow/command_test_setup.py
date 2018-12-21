# Set up the testing environment for PyVDrive commands
from pyvdrive.interface.gui.mantidipythonwidget import MantidIPythonWidget
import os
import sys
import shutil
from pyvdrive.interface import vcommand_processor
from pyvdrive.interface.VDrivePlot import VdriveMainWindow
import time
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
        self._command_process_window = self._main_window.menu_workspaces_view()

        self._command_history = list()

        # create main application
        self._command_process = vcommand_processor.VdriveCommandProcessor(self._main_window,
                                                                          self._main_window.get_controller())

        return

    @property
    def main_window(self):
        """
        return the main window's handler
        :return:
        """
        return self._command_process_window

    def run_command(self, vdrive_command):
        """
        execute a command
        :param vdrive_command:
        :return:
        """
        start_time = time.time()
        status, err_msg = self._command_process.process_commands(vdrive_command)
        stop_time = time.time()

        if status:
            message = 'Test {}\nExecution (wall) time = {}'.format(vdrive_command, stop_time-start_time)
            print (message)
            self._command_process_window.write_general_message(message)
        else:
            message = 'Test Failed: {}\nFailure cause: {}'.format(vdrive_command, err_msg)
            print (message)
            self._command_process_window.write_failure_message(message)

        self._command_process_window.set_log_tab(tab='error')

        return

    @staticmethod
    def show_output_files(output_dir):
        """
        list the output files in pretty mode
        :param output_dir:
        :return:
        """
        pretty = ''

        if os.path.exists(output_dir):
            file_names = os.listdir(output_dir)
            for index, file_name in enumerate(sorted(file_names)):
                pretty += '%-30s' % file_name
                if (index + 1) % 3 == 0:
                    pretty += '\n'
            # END-FOR
        else:
            pretty += 'Directory {} does not exist'.format(output_dir)

        print (pretty)

        return


# END-DEF-CLASS


def set_test_dir(test_dir):
    """ create directory for testing
    """
    assert isinstance(test_dir, str), 'Directory for testing result shall be a string.'

    # clean old ones
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

    # create new
    os.mkdir(test_dir)

    print ('Set up {} for testing'.format(test_dir))

    return
