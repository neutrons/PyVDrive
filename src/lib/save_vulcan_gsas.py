import mantid.simpleapi as api
from mantid.api import AnalysisDataService as ADS
import os
from datetime import datetime
import os.path


def save_gsas_temp(gsas_ws_name, gda_file_name, binning_parameters):
    """ Save file
    """
    api.Rebin(InputWorkspace=gsas_ws_name, OutputWorkspace=gsas_ws_name, Params=binning_parameters)

    # Convert from PointData to Histogram
    #  gsas_ws_name = api.ConvertToHistogram(InputWorkspace=gsas_ws_name, OutputWorkspace=str(gsas_ws_name))

    # Save
    api.SaveGSS(InputWorkspace=gsas_ws_name, Filename=gda_file_name, SplitFiles=False, Append=False,
                Format="SLOG", MultiplyByBinWidth=False, ExtendedHeader=False, UseSpectrumNumberAsBankID=True)

    return gda_file_name


def _rewrite_gda_file(self, gssfilename, newheader):
    """
    Re-write GSAS file including header and header for each bank
    :param gssfilename:
    :param newheader:
    :return:
    """
    # Get all lines
    gfile = open(gssfilename, "r")
    lines = gfile.readlines()
    gfile.close()

    # New file
    filebuffer = ""
    filebuffer += newheader

    inbank = False
    banklines = []
    for line in lines:
        cline = line.strip()
        if len(cline) == 0:
            continue

        if line.startswith("BANK"):
            # Indicate a new bank
            if len(banklines) == 0:
                # bank line for first bank
                inbank = True
                banklines.append(line.strip("\n"))
            else:
                # bank line for non-first bank.
                tmpbuffer = self._rewriteOneBankData(banklines)
                filebuffer += tmpbuffer
                banklines = [line]
                # ENDIFELSE
        elif inbank is True and cline.startswith("#") is False:
            # Write data line
            banklines.append(line.strip("\n"))

    # ENDFOR

    if len(banklines) > 0:
        tmpbuffer = self._rewriteOneBankData(banklines)
        filebuffer += tmpbuffer
    else:
        raise NotImplementedError("Impossible to have this")

    # Overwrite the original file
    ofile = open(gssfilename, "w")
    ofile.write(filebuffer)
    ofile.close()

    return


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
    curr_bank_lines = ''
    header_lines = ''
    curr_bank_id = -1
    primary_path_line = ''
    geometry_line = ''
    bank_data_dict = dict()

    for line in raw_lines:
        # skip empty line
        cline = line.strip()
        if len(cline) == 0:
            continue

        # identify geometry information lines
        if line.count('Primary') == 1:
            # primary path line
            primary_path_line = line
        elif line.count('L2') == 1:
            # secondary geometry line
            geometry_line = line
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
            curr_bank_lines = primary_path_line
            curr_bank_lines += geometry_line
            curr_bank_lines += line

            # get the current bank ID
            curr_bank_id = int(cline.split('BANK')[1].split()[0])
        elif inside_bank is True and cline.startswith("#") is False:
            # Write data line
            curr_bank_lines += line

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
    header_lines = ''

    for binning_parameters in binning_parameter_dict:
        # save GSAS to single bank temporary file
        save_gsas_temp(diffraction_workspace_name, output_file_name, binning_parameters)
        header_lines, gsas_bank_dict = read_gsas_file(output_file_name)

        # load the GSAS file and convert the header
        bank_id_list = binning_parameter_dict[binning_parameters]
        for bank_id in bank_id_list:
            bank_buffer_dict[bank_id] = gsas_bank_dict[bank_id]
        # END-FOR
    # END-FOR (binning_parameters)

    # form final output buffer
    # original header
    vulcan_gss_buffer = header_lines

    # VDRIVE special header
    diff_ws = ADS.retrieve(diffraction_workspace_name)
    header = generate_vulcan_gda_header(diff_ws, gsas_file_name=output_file_name, ipts=ipts,
                                        gsas_param_file_name=gsas_param_file)
    vulcan_gss_buffer += header

    # append each bank
    for bank_id in sorted(bank_buffer_dict.keys()):
        vulcan_gss_buffer += bank_buffer_dict[bank_id]
    # END-FOR

    # save GSAS file
    try:
        gsas_file = open(output_file_name, 'w')
        gsas_file.write(vulcan_gss_buffer)
        gsas_file.close()
    except OSError as os_err:
        raise RuntimeError('Unable to write to {0} due to {1}'.format(output_file_name, os_err))

    return
