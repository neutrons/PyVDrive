#!/usr/bin/python
"""
chop a single crystal run and provide tool to visualize it
"""
import getopt
import os
import sys
from pyvdrive.lib import mantid_reduction
from pyvdrive.lib import mantid_helper
from pyvdrive.lib import vulcan_util
import random
from pyvdrive.lib import datatypeutility
from pyvdrive.lib import archivemanager


def generate_list_csv(file_workspace_list, csv_file_name):
    """ generate a csv file for file name and workspace
    :param file_workspace_list:
    :param csv_file_name:
    :return:
    """
    # check
    datatypeutility.check_file_name(csv_file_name, check_exist=False,
                                    check_writable=True, note='Sliced NeXus file list')
    datatypeutility.check_list('File name workspace tuples', file_workspace_list)

    # write file
    write_buffer = '# NeXus file name, Workspace name\n'
    for index in range(len(file_workspace_list)):
        file_name, workspace_name = file_workspace_list[index]
        write_buffer += '{0}, {1}\n'.format(file_name, workspace_name)
    # END-FOR

    csv_file = open(csv_file_name, 'w')
    csv_file.write(write_buffer)
    csv_file.close()

    return


def get_help(cmd):
    """
    get help
    example: cmd = 'VBIN,IPTS=21356,RUNS=161972,version=2,output=\'/tmp/ver2\''
    :param cmd: name of command/executable
    :return:
    """
    help_str = ''
    help_str += '{0} is to chop a single crystal run by constant time intervals.\n'.format(cmd)
    help_str += 'Result will be saved to a series of Mantid-format NeXus files.\n'
    help_str += 'A series of PNG files will be generated for each time slice\'s counts on all 3 banks.\n'
    help_str += '\nExamples:\n'
    help_str += '> {0} --ipts=21356 --run=161972 --output=~/temp/mydata/ --time=60\n'.format(cmd)
    help_str += 'Time bin is in unit of second'

    return help_str


def main(argv):
    """
    main method
    :param argv:
    :return:
    """
    # process and parse inputs
    status, opts, args = process_inputs(argv)
    if not status:
        sys.exit(-1)

    status, arg_dict = parse_argv(opts, argv)
    if not status:
        sys.exit(-1)
    elif arg_dict is None:
        sys.exit(1)

    # load data
    ipts_number = arg_dict['ipts']
    run_number = arg_dict['run']
    try:
        nexus_file_name = archivemanager.DataArchiveManager(instrument='VULCAN'
                                                            ).get_event_file(ipts_number, run_number, True)
        data_ws_name = 'VULCAN_{0}_events'.format(run_number)
        mantid_helper.load_nexus(data_file_name=nexus_file_name, output_ws_name=data_ws_name, meta_data_only=False)
    except RuntimeError as run_err:
        print (run_err)
        sys.exit(-1)

    # slice
    ref_id = random.randint(1, 10000)
    slicer_name = 'time_slicer_{0}'.format(ref_id)
    slicer_info_table = slicer_name + '_info'
    mantid_helper.generate_event_filters_by_time(data_ws_name, splitter_ws_name=slicer_name,
                                                 info_ws_name=slicer_info_table,
                                                 start_time=None, stop_time=None,
                                                 delta_time=arg_dict['time'], time_unit='second')

    status, chop_list = mantid_helper.split_event_data(data_ws_name, split_ws_name=slicer_name,
                                                       info_table_name=slicer_info_table,
                                                       target_ws_name='slicer_{0}_ref{1}'.format(run_number, ref_id),
                                                       tof_correction=False, output_directory=arg_dict['output'],
                                                       delete_split_ws=False)
    if not status:
        print ('Failed to split event data. No output!')
        sys.exit(-1)

    # generate info csv
    csv_file_name = os.path.join(arg_dict['output'], 'README.csv')
    generate_list_csv(chop_list, csv_file_name)

    # create detector views
    generate_detector_view(chop_list)

    return


def generate_detector_view(file_ws_list):
    """ generate detector view to images
    :param file_ws_list:
    :return:
    """
    import numpy
    import matplotlib
    from matplotlib import pyplot as plt

    datatypeutility.check_list('File name/workspace name list', file_ws_list)

    for file_name, ws_name in file_ws_list:
        # workspace = mantid_helper.load_nexus_processed(file_name, ws_name)
        workspace = mantid_helper.retrieve_workspace(ws_name, raise_if_not_exist=True)
        output_dir = os.path.dirname(file_name)

        for bank_id in range(1, 8):

            if bank_id < 7:
                # get 2D array
                det_data_we = numpy.ndarray(shape=(7, 153), dtype='float')
                ws_index_we = (bank_id-1) * 7 * 153
                for j in range(153):
                    for i in range(7):
                        det_data_we[i, j] = workspace.readY(ws_index_we)[0]
                        ws_index_we += 1
                # plot
                fig_we = plt.figure(figsize=(16, 9))
                ax = fig_we.add_subplot(111)
                plt.imshow(det_data_we, origin='lower')
                plt.title('{0}: West/East Bank {1} of 7'.format(file_name, bank_id))
                ax.set_aspect('auto')

                # save
                png_name = '{0}_west_east_bank{1}.png'.format(workspace, bank_id)
                plt.savefig(os.path.join(output_dir, png_name))
                # print ('[INFO] Save bank {0} to {1}'.format(bank_id, png_name))

            elif bank_id == 7:
                # last bank (7)
                # get 2D array
                det_data = numpy.ndarray(shape=(256, 72), dtype='float')
                ws_index = 6468
                for j in range(72):
                    for i in range(256):
                        det_data[i, j] = workspace.readY(ws_index)[0]
                        ws_index += 1

                # plot
                fig = plt.figure(figsize=(16, 9))
                ax = fig.add_subplot(111)
                plt.imshow(det_data, origin='lower')
                plt.colorbar()
                ax.set_aspect('auto')
                plt.title('{0}: high angle bank'.format(file_name))

                plt.savefig(os.path.join(output_dir, '{0}_high_angle.png').format(workspace))
            # END-IF

            # close
            plt.clf()
            plt.close()
            plt.cla()

        # END-FOR
    # END-FOR

    return


def process_inputs(argv):
    """

    :param argv:
    :return:
    """
    try:
        print argv
        opts, args = getopt.getopt(argv[1:], '', ['help', 'ipts=', "run=", 'output=', 'time='])
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
    if len(argv) <= 1:
        print ('Run "{0} --help" to see help information'.format(argv[0]))
        return False, None

    # init return dictionary
    setup_dict = {'ipts': None,
                  'run': None,
                  'output': None,
                  'time': None}

    # parse!
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            # Help
            print (get_help(argv[0]))
            return True, None

        elif opt == '--ipts':
            # IPTS number Input NeXus file
            setup_dict['ipts'] = int(arg)

        elif opt == '--run':
            # Run number
            setup_dict['run'] = int(arg)

        elif opt == '--output':
            # output dir
            setup_dict['output'] = str(arg)

        elif opt == '--time':
            # time slicer
            setup_dict['time'] = float(arg)

        else:
            print ('[ERROR] Option {0} with value {1} is not recoganized'.format(opt, arg))
    # END-FOR

    # check
    for arg_key in setup_dict:
        if setup_dict[arg_key] is None:
            print ('Option {0} must be given!'.format(arg_key))
            return False, None
    # END-IF

    if setup_dict['output'].startswith('~'):
        setup_dict['output'] = os.path.expanduser(setup_dict['output'])

    return True, setup_dict


if __name__ == '__main__':
    main(sys.argv)
