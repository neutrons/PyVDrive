"""
VCHROP
"""
import os
from process_vcommand import VDriveCommandProcessor


class VdriveChop(VDriveCommandProcessor):
    """
    Process command MERGE
    """
    SupportedArgs = ['IPTS', 'RUNS', 'RUNE', 'dbin', 'loadframe', 'bin', 'pickdate']

    def __init__(self, controller, command_args):
        """ Initialization
        """
        VDriveCommandProcessor.__init__(self, controller, command_args)

        self.check_command_arguments(self.SupportedArgs)
        
        return

    def exec(self):
        """ Execute input command
        """
        # parse
        try:
            ipts_number = int(self._commandArgList['IPTS'])
            run_start = int(self._commandArgList['RUNS'])
            run_end = int(self._commandArgList['RUNE'])

        except KeyError as err:
            raise RuntimeError('MERGE command requires input of argument %s.' % dd)

        blabla

