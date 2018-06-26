"""
chop a single crystal run and provide tool to visualize it
"""
import getopt
import os
import sys
from pyvdrive.lib import mantid_reduction




def get_help(cmd):
    """
    get help
    :param cmd: name of command/executable
    :return:
    """
    help_str = ''
    help_str += '{0} is to do time-focus on single crystal peaks with a user-provided Region-of-Interest ' \
                'file.\n'.format(cmd)
    help_str += 'The input will be given by a CSV file that contains a list of NeXus files to do time focus.\n'
    help_str += 'Result will be saved to a series of ASCII column files.\n'
    help_str += 'It is the second step operation in single crystal peak reduction.\n'
    help_str += '\nExamples:\n'
    help_str += '> {0}--input=~/temp/mychopped/filelist.csv  --roi=~/temp/roi.xml ' \
                '--calibration=/SNS/VULCAN/shared/CALIBRATION/....' \
                ' --output=~/temp/myfocus/ --time=60\n'

    return help_str


def main(argv):
    """
    main method
    :param argv:
    :return:
    """
    


    return


def process_inputs(argv):
    """

    :param argv:
    :return:
    """
    try:
        opts, args = getopt.getopt(argv, "h:o:", ["help", "input=", "roi=", 'output=', 'calibration='])
    except getopt.GetoptError:
        print "Exception: %s" % (str(getopt.GetoptError))
        return False, None, None

    return True, opts, args


def parse_argv(opts, argv):
    """ Parse arguments and put to dictionary
    :param opts:
    :param argv:
    :return:
    """
    # process input arguments in 2 different modes: auto-reduction and manual reduction (options)
    if len(argv) == 0:
        print ('Run "{0} --help" to see help information')
        return False, None

    # init return dictionary
    setup_dict = {'input': None,
                  'calibration': None,
                  'output': None,
                  'roi': None}

    # parse!
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            # Help
            print (get_help(argv[0]))
            return True, None

        elif opt == '--input':
            # IPTS number Input NeXus file
            setup_dict['input'] = int(arg)

        elif opt == '--calibration':
            # Run number
            setup_dict['calibration'] = int(arg)

        elif opt == '--output':
            # output dir
            setup_dict['output'] = str(arg)

        elif opts == '--roi':
            # time slicer
            setup_dict['roi'] = float(arg)
        else:
            print ('[ERROR] Option {0} with value {1} is not recoganized'.format(opt, arg))
    # END-FOR

    # check
    for arg_key in setup_dict:
        if setup_dict[argv] is None:
            print ('Option {0} must be given!'.format(arg_key))
            return False, None
    # END-IF

    return True, setup_dict


if __name__ == '__main__':
    main(sys.argv)