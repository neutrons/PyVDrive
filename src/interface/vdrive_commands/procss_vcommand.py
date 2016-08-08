"""
Base class for VDRIVE command processors
"""


class VDriveCommandProcessor(object):
    """
    Base class to process VDRIVE commands
    """
    def __init__(self, controller, command_args):
        """
        """
        assert isinstance(controller, VdriveAPI)
        assert isinstance(command_args, dict)

        # set controller
        self._controller = controller

        # set arguments
        self._commandArgList = command_args

        return

    def exec(self):
        """
        """
        raise NotImplementedError('This method must be override')

    def check_command_arguments(self, supported_arg_list):
        """ Check whether the command arguments are valid
        """
        # check whether the any non-supported args
        input_args = self._commandArgList.keys()
        for arg_key in input_args:
            if arg_key not in supported_arg_list:
                raise KeyError('VBIN argument %s is not recognized.' % arg_key)
        # END-FOF
