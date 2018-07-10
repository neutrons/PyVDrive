#!/usr/bin/python
"""
chop a single crystal run and provide tool to visualize it
"""
import getopt
import os
import sys
from pyvdrive.lib import mantid_reduction
from pyvdrive.lib import mantid_helper
from pyvdrive.lib import datatypeutility
import csv


def read_csv(csv_file_name):
    """
    read input csv for data
    :param csv_file_name:
    :return:
    """
    # check input
    datatypeutility.check_file_name(csv_file_name, check_exist=True, check_writable=False,
                                    note='NeXus file Output Workspace Name File')

    file_workspace_list = list()

    if False:
        with open(csv_file_name, 'r') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',', quotechar='#')
            for row in csv_reader:
                print type(row), len(row)
                print row
    else:
        csv_file = open(csv_file_name, 'r')
        lines = csv_file.readlines()
        csv_file.close()
        for line in lines:
            line = line.strip()
            if line.startswith('#'):
                continue

            terms = line.split(',')
            file_name = terms[0].strip()
            ws_name = terms[1].strip()
            file_workspace_list.append((file_name, ws_name))

    return file_workspace_list


def get_help(cmd):
    """
    get help:
    Example: pyvdrivescript.sh --input=~/Temp/mydata/README.csv --roi=sample_roi.xml
        --calibration=/SNS/VULCAN/shared/CALIBRATION/2018_6_1_CAL/VULCAN_calibrate_2018_06_01.h5
        --output=~/Temp/mydata/reduced
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
    # TODO FIXME - Make it right!
    help_str += '> {0} --input=~/Temp/mydata/README.csv --roi=sample_roi.xml ' \
                '--calibration=/SNS/VULCAN/shared/CALIBRATION/2018_6_1_CAL/VULCAN_calibrate_2018_06_01.h5 ' \
                '--output=~/Temp/mydata/reduced\n'.format(cmd)

    return help_str


def main(argv):
    """
    main method
    :param argv:
    :return:
    """
    # process inputs
    status, opts, args = process_inputs(argv)
    if not status:
        sys.exit(-1)

    status, setup_dict = parse_argv(opts, argv)
    if not status:
        sys.exit(-1)
    elif setup_dict is None:
        sys.exit(1)

    # parse input file
    nexus_workspace_list = read_csv(setup_dict['input'])

    # define calibration
    root_name = 'vulcan'
    calib_ws_name = 'vulcan_cal'
    group_ws_name = 'vulcan_group'
    mask_ws_name = None

    # do diffraction focus
    for index in range(len(nexus_workspace_list)):
        # get file and data workspace name
        nexus_file_name, data_ws_name = nexus_workspace_list[index]

        # load data
        mantid_helper.load_nexus(data_file_name=nexus_file_name,
                                 output_ws_name=data_ws_name,
                                 meta_data_only=False)

        # load calibration for the first time
        if index == 0:
            # load calibration
            mantid_helper.load_calibration_file(calib_file_name=setup_dict['calibration'],
                                                output_name=root_name,
                                                ref_ws_name=data_ws_name)

            # load region of interest file
            mask_ws_name = mantid_helper.load_roi_xml(data_ws_name, roi_file_name=setup_dict['roi'])

        mantid_reduction.align_and_focus_event_ws(event_ws_name=data_ws_name,
                                                  output_ws_name=data_ws_name,
                                                  binning_params='0.3,-0.0003,5.0',
                                                  diff_cal_ws_name=calib_ws_name,
                                                  mask_ws_name=mask_ws_name,
                                                  grouping_ws_name=group_ws_name,
                                                  keep_raw_ws=False,
                                                  convert_to_matrix=True,
                                                  reduction_params_dict=dict())

        # save!
        output_dir = setup_dict['output']
        mantid_helper.save_event_workspace(data_ws_name, os.path.join(output_dir, data_ws_name + '.nxs'))
        mantid_reduction.save_ws_ascii(data_ws_name, output_dir, data_ws_name)
    # END-FOR

    return


def process_inputs(argv):
    """

    :param argv:
    :return:
    """
    try:
        opts, args = getopt.getopt(argv[1:], "h:o:", ["help", "input=", "roi=", 'output=', 'calibration='])
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
    cmd = 'vulcan.' + os.path.basename(argv[0]).split('.')[0]
    if len(argv) <= 1:
        print ('Run "{0} --help" to see help information'.format(cmd))
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
            print (get_help(cmd))
            return True, None

        elif opt == '--input':
            # IPTS number Input NeXus file
            setup_dict['input'] = str(arg)

        elif opt == '--calibration':
            # Run number
            setup_dict['calibration'] = str(arg)

        elif opt == '--output':
            # output dir
            setup_dict['output'] = str(arg)

        elif opt == '--roi':
            # time slicer
            setup_dict['roi'] = str(arg)
        else:
            print ('[ERROR] Option {0} with value {1} is not recoganized'.format(opt, arg))
    # END-FOR

    # check
    for arg_key in setup_dict:
        if setup_dict[arg_key] is None:
            print ('Option {0} must be given!'.format(arg_key))
            return False, None
    # END-IF

    for arg_key in ['input', 'roi', 'calibration', 'output']:
        if setup_dict[arg_key].startswith('~'):
            setup_dict[arg_key] = os.path.expanduser(setup_dict[arg_key])

    # if setup_dict['input'].startswith('~'):
    #     setup_dict['input'] = os.path.expanduser(setup_dict['input'])
    # if setup_dict['roi'].startswith('~'):
    #     setup_dict['roi'] = os.path.expanduser(setup_dict['roi'])

    return True, setup_dict


if __name__ == '__main__':
    main(sys.argv)
