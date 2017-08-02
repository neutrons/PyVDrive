import mantid.simpleapi as api
from mantid.api import AnalysisDataService as ADS
import os


def save_gsas_temp(gsas_ws_name, gda_file_name, binning_parameters):
    """ Save file
    """
    print '[DB] Binning: {0}'.format(binning_parameters)
    api.Rebin(InputWorkspace=gsas_ws_name, OutputWorkspace=gsas_ws_name, Params=binning_parameters)

    # Convert from PointData to Histogram
    #  gsas_ws_name = api.ConvertToHistogram(InputWorkspace=gsas_ws_name, OutputWorkspace=str(gsas_ws_name))

    # Save
    api.SaveGSS(InputWorkspace=gsas_ws_name, Filename=gda_file_name, SplitFiles=False, Append=False,
                Format="SLOG", MultiplyByBinWidth=False, ExtendedHeader=False, UseSpectrumNumberAsBankID=True)

    gsas_ws = ADS.retrieve(gsas_ws_name)

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
    """
    from datetime import datetime
    import os.path

    # TODO/CHECK/ISSUE/NOWNOW

    # Get necessary information
    title = gsas_workspace.getTitle()

    run = gsas_workspace.getRun()

    # Get information on start/stop
    processtime = True
    if run.hasProperty("run_start") and run.hasProperty("duration"):
        runstart = run.getProperty("run_start").value
        duration = float(run.getProperty("duration").value)
    else:
        processtime = False

    if processtime is True:
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


def _rewriteOneBankData(banklines):
    """ first line is for bank information
    """
    wbuf = ""

    # Rewrite bank lines
    bankline = banklines[0].strip()
    terms = bankline.split()
    tofmin = float(banklines[1].split()[0])
    tofmax = float(banklines[-1].split()[0])

    terms[5] = "%.1f" % (tofmin)
    terms[6] = "%.1f" % (tofmax)

    newbankline = ""

    # title
    for t in terms:
        newbankline += "%s " % (t)
    wbuf = "%-80s\n" % (newbankline)

    # data
    for i in range(1, len(banklines)):
        cline = banklines[i]

        terms = cline.split()
        try:
            tof = float(terms[0])
            y = float(terms[1])
            e = float(terms[2])

            x_s = "%.1f" % (tof)
            y_s = "%.1f" % (y)
            e_s = "%.2f" % (e)

            temp = "%12s%12s%12s" % (x_s, y_s, e_s)

        except TypeError:
            temp = "%-80s\n" % (cline.rstrip())

        wbuf += "%-80s\n" % (temp)
    # ENDFOR

    return wbuf


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

    # cut the GSAS file into multiple sections by BANK
    inside_bank = False
    curr_bank_lines = list()
    header_lines = list()
    curr_bank_id = -1
    bank_data_dict = dict()

    for line in raw_lines:
        cline = line.strip()
        if len(cline) == 0:
            continue
        cline = line.strip('\n')

        if cline.startswith("BANK"):
            # Indicate a new bank
            if len(curr_bank_lines) == 0:
                # first bank in the GSAS file
                inside_bank = True
                curr_bank_lines.append(cline)

            else:
                # bank line for next bank. need to process the previous-current bank
                bank_data_dict[curr_bank_id] = curr_bank_lines
                curr_bank_lines = [line]
            # ENDIFELSE

            # get the current bank ID
            curr_bank_id = int(cline.split('BANK')[1].split()[0])

        elif inside_bank is True and cline.startswith("#") is False:
            # Write data line
            curr_bank_lines.append(cline)

        elif inside_bank is False:
            # must be header
            header_lines.append(cline)
        # END-IF-ELSE
    # END-FOR

    if len(curr_bank_lines) > 0:
        bank_data_dict[curr_bank_id] = curr_bank_lines
    else:
        raise NotImplementedError("Impossible to have this")

    return header_lines, bank_data_dict


def save_vulcan_gss(diffraction_workspace_name, binning_parameter_dict, output_file_name, ipts, gsas_param_file):
    """

    :param diffraction_workspace_name:
    :param binning_parameter_dict:
    :param output_file_name:
    :param ipts:
    :param gsas_param_file:
    :return:
    """
    # save to a general GSAS files and load back for the data portion
    bank_buffer_dict = dict()
    header_lines = list()

    for binning_parameters in binning_parameter_dict:
        # save GSAS to single bank temporary file
        save_gsas_temp(diffraction_workspace_name, output_file_name, binning_parameters)
        header_lines, gsas_bank_dict = read_gsas_file(output_file_name)

        # load the GSAS file and convert the header
        bank_id_list = binning_parameter_dict[binning_parameters]
        print '[DB...BAT] Bank List: {0}'.format(bank_id_list)
        for bank_id in bank_id_list:
            bank_buffer_dict[bank_id] = gsas_bank_dict[bank_id]
        # END-FOR
    # END-FOR (binning_parameters)

    # form final output buffer
    vulcan_gss_buffer = ''
    for line in header_lines:
        if line.startswith('#'):
            vulcan_gss_buffer += line + '\n'

    diff_ws = ADS.retrieve(diffraction_workspace_name)
    header = generate_vulcan_gda_header(diff_ws, gsas_file_name=output_file_name, ipts=ipts,
                                        gsas_param_file_name=gsas_param_file)
    vulcan_gss_buffer += header

    for bank_id in sorted(bank_buffer_dict.keys()):
        for line in bank_buffer_dict[bank_id]:
            vulcan_gss_buffer += line + '\n'  # bank_buffer_dict[bank_id]
        # END-FOR
    # END-FOR

    # save GSAS file
    try:
        gsas_file = open(output_file_name, 'w')
        gsas_file.write(vulcan_gss_buffer)
        gsas_file.close()
    except OSError as os_err:
        raise RuntimeError('Unable to write to {0} due to {1}'.format(output_file_name, os_err))

    return







