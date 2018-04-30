#!/usr/bin/python
# Test the chop and reduce command
from pyvdrive.lib import *
from pyvdrive.interface import *
from pyvdrive.interface.vdrive_commands import *

import command_test_setup

command_tester = command_test_setup.Tester()

command_tester.run_command('chop, ipts=????, runs=????, delta_time=????, output=????')
