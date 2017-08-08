import sys
sys.path.append("/opt/mantidnightly/bin")

import mantid.simpleapi as api
from mantid.api import AnalysisDataService as ADS
import os
from datetime import datetime
import os.path


def save_mantid_gsas(gsas_ws_name, gda_file_name, binning_parameters):
    """
    Save temporary GSAS file
    :param gsas_ws_name:
    :param gda_file_name:
    :param binning_parameters:
    :return:
    """
    if binning_parameters is not None:
        api.Rebin(InputWorkspace=gsas_ws_name, OutputWorkspace=gsas_ws_name, Params=binning_parameters)

    # Convert from PointData to Histogram
    #  gsas_ws_name = api.ConvertToHistogram(InputWorkspace=gsas_ws_name, OutputWorkspace=str(gsas_ws_name))

    # Save
    api.SaveGSS(InputWorkspace=gsas_ws_name, Filename=gda_file_name, SplitFiles=False, Append=False,
                Format="SLOG", MultiplyByBinWidth=False, ExtendedHeader=False, UseSpectrumNumberAsBankID=True)

    return gda_file_name


def reformat_gsas_bank(bank_line_list):
    """
    re-format all the lines to GSAS/VDRive compatible
    :param bank_line_list:
    :return:
    """
    # check input
    assert isinstance(bank_line_list, list), 'Bank lines must be given by list.'
    if len(bank_line_list) < 4:
        raise RuntimeError('Number of lines in bank data {0} is too small.'.format(len(bank_line_list)))

    # init
    bank_data = ''
    in_data = False
    i_line = 0

    # add the information lines till 'BANK'
    while in_data is False and i_line < len(bank_line_list):
        # current line
        curr_line = bank_line_list[i_line]

        if curr_line.count('BANK') == 1:
            # bank line. need reformat
            in_data = True

            # form the new BANK line
            tof_min = float(bank_line_list[i_line+1].split()[0])
            tof_max = float(bank_line_list[-1].split()[0])

            terms = curr_line.split()
            # replace TOF min and TOF max (item 5 and 6)
            terms[5] = "%.1f" % tof_min
            terms[6] = "%.1f" % tof_max

            new_bank_line = ''
            for t in terms:
                new_bank_line += "%s " % t
            bank_data += "%-80s\n" % new_bank_line
        else:
            # regular geometry line
            bank_data += '{0}'.format(bank_line_list[i_line])
        i_line += 1
    # END-WHILE

    # scan data
    for i in range(i_line, len(bank_line_list)):
        # split the line
        terms = bank_line_list[i].strip().split()
        try:
            tof = float(terms[0])
            y = float(terms[1])
            e = float(terms[2])
            x_s = "%.1f" % tof
            y_s = "%.1f" % y
            e_s = "%.2f" % e

            temp = "%12s%12s%12s" % (x_s, y_s, e_s)

        except TypeError:
            # unable to convert to X, Y, Z. then use the original line
            temp = "%-80s" % bank_line_list[i].rstrip()
        except ValueError:
            # unable to convert to X, Y, Z
            temp = '%-80s' % bank_line_list[i].rstrip()
            print '[ERROR] Unexpected line {0}: {1} as data.'.format(i, temp)
        # END-TRY-EXCEPTION

        bank_data += "%-80s\n" % temp
    # END-FOR

    return bank_data


def generate_vulcan_gda_header(gsas_workspace, gsas_file_name, ipts, gsas_param_file_name):
    """
    generate a VDRIVE compatible GSAS file's header
    :param gsas_workspace:
    :param gsas_file_name:
    :param ipts:
    :param gsas_param_file_name:
    :return: string : multiple lines
    """
    # check
    assert isinstance(gsas_workspace, str) is False, 'GSAS workspace must not be a string.'
    assert isinstance(gsas_file_name, str), 'GSAS file name {0} must be a string.'.format(gsas_file_name)
    assert isinstance(ipts, int) or isinstance(ipts, str), 'IPTS number {0} must be either string or integer.' \
                                                           ''.format(ipts)
    assert isinstance(gsas_param_file_name, str), 'GSAS iparm file name {0} must be an integer.' \
                                                  ''.format(gsas_param_file_name)
    if isinstance(ipts, str):
        assert ipts.isdigit(), 'IPTS {0} must be convertible to an integer.'.format(ipts)

    # Get necessary information
    print '[DB...BAT] Type of GSAS workspace: {0}'.format(type(gsas_workspace))
    title = gsas_workspace.getTitle()
    run = gsas_workspace.getRun()

    # Get information on start/stop
    if run.hasProperty("run_start") and run.hasProperty("duration"):
        # export processing time information
        runstart = run.getProperty("run_start").value
        duration = float(run.getProperty("duration").value)
        # property run_start and duration exist
        runstart_sec = runstart.split(".")[0]
        runstart_ns = runstart.split(".")[1]

        utctime = datetime.strptime(runstart_sec, '%Y-%m-%dT%H:%M:%S')
        time0 = datetime.strptime("1990-01-01T0:0:0", '%Y-%m-%dT%H:%M:%S')

        delta = utctime - time0
        try:
            total_nanosecond_start = int(delta.total_seconds() * int(1.0E9)) + int(runstart_ns)
        except AttributeError:
            total_seconds = delta.days * 24 * 3600 + delta.seconds
            total_nanosecond_start = total_seconds * int(1.0E9) + int(runstart_ns)
        total_nanosecond_stop = total_nanosecond_start + int(duration * 1.0E9)
    else:
        # not both property is found
        total_nanosecond_start = 0
        total_nanosecond_stop = 0

    # Construct new header
    newheader = ""

    if len(title) > 80:
        title = title[0:80]
    newheader += "%-80s\n" % title

    newheader += "%-80s\n" % ("Instrument parameter file: %s" % gsas_param_file_name)

    newheader += "%-80s\n" % ("#IPTS: %s" % str(ipts))

    newheader += "%-80s\n" % "#binned by: Mantid"

    newheader += "%-80s\n" % ("#GSAS file name: %s" % os.path.basename(gsas_file_name))

    newheader += "%-80s\n" % ("#GSAS IPARM file: %s" % gsas_param_file_name)

    newheader += "%-80s\n" % ("#Pulsestart:    %d" % total_nanosecond_start)

    newheader += "%-80s\n" % ("#Pulsestop:     %d" % total_nanosecond_stop)

    return newheader


def read_gsas_file(gsas_file_name):
    """read GSAS file
    :param gsas_file_name:
    :return: 2-tuple (1) list as headers (2) a dictionary: key = bank ID, value = list of strings (lines)
    """
    # check input
    assert isinstance(gsas_file_name, str), 'Input GSAS file name {0} must be a string.'.format(gsas_file_name)
    if os.path.exists(gsas_file_name) is False:
        raise RuntimeError('GSAS file {0} cannot be found.'.format(gsas_file_name))

    # read file to lines
    g_file = open(gsas_file_name, 'r')
    raw_lines = g_file.readlines()
    g_file.close()

    # cut the GSAS file into multiple sections by BANK.  create the strings other than list of lines
    inside_bank = False
    curr_bank_lines = list()
    header_lines = ''
    curr_bank_id = -1
    bank_geometry_line = ''
    spectrum_flag_line = ''
    bank_data_dict = dict()

    for line in raw_lines:
        # skip empty line
        cline = line.strip()
        if len(cline) == 0:
            continue

        # identify geometry information lines
        if line.count('DIFC') == 1 and line.count('path') == 1:
            # primary path line
            bank_geometry_line = line
        elif line.count('Data for spectrum') == 1:
            # secondary geometry line
            spectrum_flag_line = line
        elif line.startswith("BANK"):
            # Indicate a new bank
            if len(curr_bank_lines) == 0:
                # first bank in the GSAS file
                inside_bank = True
            else:
                # bank line for next bank. need to process the previous-current bank
                bank_data_dict[curr_bank_id] = curr_bank_lines
            # END-IF-ELSE

            # construct the first 3 lines
            curr_bank_lines = list()
            curr_bank_lines.append(bank_geometry_line)
            curr_bank_lines.append(spectrum_flag_line)
            curr_bank_lines.append(line)

            # get the current bank ID
            curr_bank_id = int(cline.split('BANK')[1].split()[0])
        elif inside_bank is True and cline.startswith("#") is False:
            # Write data line
            curr_bank_lines.append(line)

        elif inside_bank is False:
            # must be header
            header_lines += line
        # END-IF-ELSE
    # END-FOR

    if len(curr_bank_lines) > 0:
        bank_data_dict[curr_bank_id] = curr_bank_lines
    else:
        raise NotImplementedError("Impossible to have this")

    return header_lines, bank_data_dict


def save_vanadium_gss(self, vanadium_workspace_dict, out_file_name, ipts_number, gsas_param_file):
    """
    save vanadium GSAS
    :param self:
    :param vanadium_workspace_dict:
    :param out_file_name:
    :param ipts_number:
    :return:
    """
    # check input
    assert isinstance(vanadium_workspace_dict, dict), 'vanadium workspaces must be given by dictionary.'
    if len(vanadium_workspace_dict) == 0:
        raise RuntimeError('Vanadium workspace dictionary is empty.')

    # save to temporary GSAS file
    bank_buffer_dict = dict()
    # FIXME - This is not efficient because bank 1 and bank 2 always have the same resolution
    for bank_id in sorted(vanadium_workspace_dict.keys()):
        # save to a temporary file
        van_ws_name = vanadium_workspace_dict[bank_id]
        save_mantid_gsas(van_ws_name, out_file_name, None)
        header_lines, gsas_bank_dict = read_gsas_file(out_file_name)

        # load the GSAS file and convert the header
        bank_buffer_dict[bank_id] = gsas_bank_dict[bank_id]
    # END-FOR

    # form final output buffer
    # original header
    vulcan_gss_buffer = ''  # header_lines

    # VDRIVE special header
    diff_ws = ADS.retrieve(vanadium_workspace_dict.values[0])
    header = generate_vulcan_gda_header(diff_ws, gsas_file_name=out_file_name, ipts=ipts_number,
                                        gsas_param_file_name=gsas_param_file)
    vulcan_gss_buffer += header
    vulcan_gss_buffer += '%-80s\n' % '#'  # one empty comment line

    # append each bank
    for bank_id in sorted(bank_buffer_dict.keys()):
        bank_data_str = reformat_gsas_bank(bank_buffer_dict[bank_id])
        vulcan_gss_buffer += bank_data_str
    # END-FOR

    # save GSAS file
    try:
        gsas_file = open(out_file_name, 'w')
        gsas_file.write(vulcan_gss_buffer)
        gsas_file.close()
    except OSError as os_err:
        raise RuntimeError('Unable to write to {0} due to {1}'.format(out_file_name, os_err))

    return

def save_vulcan_gss(diffraction_workspace_name, binning_parameter_dict, output_file_name, ipts, gsas_param_file):
    """
    Save a diffraction workspace to GSAS file for VDRive
    :param diffraction_workspace_name:
    :param binning_parameter_dict:
    :param output_file_name:
    :param ipts:
    :param gsas_param_file:
    :return:
    """
    # default
    if binning_parameter_dict is None:
        binning_parameter_dict = {(5000., -0.001, 70000.): [1, 2],
                                  (5000., -0.0003, 70000.): [3]}

    # check
    assert isinstance(diffraction_workspace_name, str), 'Diffraction workspace name {0} must be a string.' \
                                                        ''.format(diffraction_workspace_name)
    assert isinstance(binning_parameter_dict, dict), 'Binning parameters {0} must be given in a dictionary.' \
                                                     ''.format(binning_parameter_dict)
    assert isinstance(output_file_name, str), 'Output file name {0} must be a string.'.format(output_file_name)
    output_dir = os.path.dirname(output_file_name)
    if os.path.exists(output_dir) is False:
        raise RuntimeError('Directory {0} for output GSAS file {1} does not exist.'
                           ''.format(output_dir, output_file_name))
    elif os.path.exists(output_file_name) and os.access(output_file_name, os.W_OK) is False:
        raise RuntimeError('Output GSAS file {0} exists and current user has not priviledge to overwrite it.'
                           ''.format(output_file_name))
    elif os.access(output_dir, os.W_OK) is False:
        raise RuntimeError('Current user has no writing priviledge to directory {0}'.format(output_dir))

    # save to a general GSAS files and load back for the data portion
    bank_buffer_dict = dict()
    # header_lines = ''

    for binning_parameters in binning_parameter_dict:
        # save GSAS to single bank temporary file
        save_mantid_gsas(diffraction_workspace_name, output_file_name, binning_parameters)
        header_lines, gsas_bank_dict = read_gsas_file(output_file_name)

        # load the GSAS file and convert the header
        bank_id_list = binning_parameter_dict[binning_parameters]
        for bank_id in bank_id_list:
            bank_buffer_dict[bank_id] = gsas_bank_dict[bank_id]
        # END-FOR
    # END-FOR (binning_parameters)

    # form final output buffer
    # original header
    vulcan_gss_buffer = ''  # header_lines

    # VDRIVE special header
    diff_ws = ADS.retrieve(diffraction_workspace_name)
    header = generate_vulcan_gda_header(diff_ws, gsas_file_name=output_file_name, ipts=ipts,
                                        gsas_param_file_name=gsas_param_file)
    vulcan_gss_buffer += header
    vulcan_gss_buffer += '%-80s\n' % '#'   # one empty comment line

    # append each bank
    for bank_id in sorted(bank_buffer_dict.keys()):
        bank_data_str = reformat_gsas_bank(bank_buffer_dict[bank_id])
        vulcan_gss_buffer += bank_data_str
    # END-FOR

    # save GSAS file
    try:
        print '[DB...BAT] WRITE OUT FINAL GSAS File {0}.'.format(output_file_name)
        gsas_file = open(output_file_name, 'w')
        gsas_file.write(vulcan_gss_buffer)
        gsas_file.close()
    except OSError as os_err:
        raise RuntimeError('Unable to write to {0} due to {1}'.format(output_file_name, os_err))

    return
