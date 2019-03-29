# Set up the testing environment for PyVDrive commands
from pyvdrive.interface.gui.mantidipythonwidget import MantidIPythonWidget
import os
import sys
import shutil
import filecmp
from pyvdrive.interface import vcommand_processor
from pyvdrive.interface.VDrivePlot import VdriveMainWindow
from pyvdrive.lib import datatypeutility
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
        """ Execute a VDRIVE IDL command
        BY calling vcommand_processor.process_command()
        It WON'T leave any history on IPython console
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

        # always let user to look at the failed tab even if there is no error
        self._command_process_window.set_log_tab(tab='error')

        return

    def show_output_files(self, output_dir):
        """
        list the output files in pretty mode
        :param output_dir:
        :return:
        """
        pretty = '{}:\n'

        if os.path.exists(output_dir):
            file_names = os.listdir(output_dir)
            for index, file_name in enumerate(sorted(file_names)):
                pretty += '%-30s' % file_name
                if (index + 1) % 3 == 0:
                    pretty += '\n'
            # END-FOR
        else:
            pretty += 'Directory {} does not exist'.format(output_dir)

        self._command_process_window.write_general_message(pretty)
        self._command_process_window.set_log_tab(tab='info')

        return

    def examine_result(self, generated_files, gold_files):
        """ Examine the system test result (GSAS files) against pre-specified golden files
        :param generated_files:
        :param gold_files:
        :return:
        """
        datatypeutility.check_list('PyVDrive system test - generated GSAS files', generated_files)
        datatypeutility.check_list('PyVDrive system test - gold GSAS files', gold_files)
        if len(generated_files) != len(gold_files):
            raise RuntimeError('Test-generated files do not have 1-to-1 map to test-gold files')

        test_passed = True
        message = ''
        for i_file in range(len(generated_files)):
            if os.path.exists(generated_files[i_file]):
                # test-file exists
                test_passed_i, message_i = self.compare_gsas_file(generated_files[i_file], gold_files[i_file])
            else:
                # test-file does not exist
                test_passed_i = False
                message_i = 'Test-generated file {} cannot be found.'.format(generated_files[i_file])
            test_passed = test_passed and test_passed_i
            message += message_i + '\n'
        # END-FOR

        if test_passed:
            self._command_process_window.write_general_message(message)
        else:
            self._command_process_window.write_failure_message(message)
        self._command_process_window.set_log_tab('error')

        return test_passed, message

    def compare_gsas_file(self, test_file, gold_file):
        """
        compare GSAS file between test-generated file and gold file
        :param test_file:
        :param gold_file:
        :return:
        """
        if filecmp.cmp(test_file, gold_file):
            # completely same
            files_same = True
            message = 'Tested generated file {} is exactly same as gold file {}'.format(test_file, gold_file)

        else:
            # not same: then find out how different
            files_same = False
            if self.get_file_lines(test_file) != self.get_file_lines(gold_file):
                # same lines?
                message = 'Tested generated file {} has different lines with gold file {} ({} vs {})' \
                          ''.format(test_file, gold_file, self.get_file_lines(test_file),
                                    self.get_file_lines(gold_file))
            elif os.path.getsize(test_file) == os.path.getsize(gold_file):  # file size in bytes
                # same size?
                message = 'Tested generated file {} has same lines but different sizes with gold file {} ({} vs {})' \
                          ''.format(test_file, gold_file, os.path.getsize(test_file),
                                    os.path.getsize(gold_file))
            else:
                # more intrinsic reason
                message = 'Tested generated file {} has different content with gold file {}' \
                          ''.format(test_file, gold_file)
        # END-IF-ELSE

        return files_same, message

    @staticmethod
    def get_file_lines(path_to_file):
        """ get number of lines in a file
        :param path_to_file:
        :return:
        """
        in_file = open(path_to_file, 'r')
        lines = in_file.readlines()
        in_file.close()

        return len(lines)

    def set_failure(self, message):
        """
        set a test failure message to error log
        :param message:
        :return:
        """
        self._command_process_window.write_failure_message(message)

    def set_success(self, message):
        """
        set a test success message to general/information log
        :param message:
        :return:
        """
        self._command_process_window.write_general_message(message)

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
