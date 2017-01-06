import os
from procss_vcommand import VDriveCommand


class VanadiumPeak(VDriveCommand):
    """ process vanadium peaks
    """
    SupportedArgs = ['IPTS', 'RUNV', 'HELP', 'Nsmooth', 'OneBank', 'Shift', 'OUTPUT']

    ArgsDocDict = {
        'IPTS': 'IPTS number',
        'RUNV': 'Run number for vanadium file (file in instrument directory)',
        'HELP': 'Launch General Plot Viewer',
        'OneBank': 'Add 2 bank data together (=1).',
        'Shift': 'the chopper center is shift to large lambda aggressively.',
        'Nsmooth': 'the number of points to be used in the boxcar smoothing algorithm.',
        'OUTPUT': 'the directory where the smooth vanadium gsas file will be saved other than default.'
    }

    def __init__(self, controller, command_args):
        """
        initialization of an object

        [Input]
        VPEAK, IPTS=1000, RUNV=5000
        Additional keyword:
        Nsmooth =51: The number of points to be used in the boxcar smoothing
             algorithm, the bigger the smoother.
        OneBank=1:  all banks data are binned as one bank data.
        Shift=1: the chopper center is shift to large lambda aggressively.

        [Output]
        The smoothed data is named as ####-s.gda and located at /SNS/VULCAN/IPTS-1000/shared/Instrument
            as well as a copy in the VULCAN shared fold

        :param controller:
        :param command_args:
        """
        super(VanadiumPeak, self).__init__(controller, command_args)

        return

    def exec_cmd(self):
        """
        Execute command: override
        """
        # ... FIXME/TODO/NOW/ISSUE/59 - From here!