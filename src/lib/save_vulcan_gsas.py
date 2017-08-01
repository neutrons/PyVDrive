import mantid.simpleapi as api
from mantid.api import AnalysisDataService as ADS


def save_gsas_temp(gsas_ws_name, gda_file_name, binning_parameters):
    """ Save file
    """
    def _find_gsas_files(gda_file_name, num_banks):
        # TODO/ISSUE/NOW - Find out the output files' names
        return list()

    api.Rebin(InputWorkspace=gda_file_name, OutputWorkspace=gda_file_name, Params=binning_parameters)

    # Convert from PointData to Histogram
    gsas_ws_name = api.ConvertToHistogram(InputWorkspace=gsas_ws_name, OutputWorkspace=str(gsas_ws_name))

    # Save
    api.SaveGSS(InputWorkspace=gsas_ws_name, Filename=gda_file_name, SplitFiles=True, Append=False,
                Format="SLOG", MultiplyByBinWidth=False, ExtendedHeader=False, UseSpectrumNumberAsBankID=True)

    gsas_ws = ADS.retrieve(gsas_ws_name)
    gsas_file_name_dict = _find_gsas_files(gda_file_name, gsas_ws.getNumberHistograms())

    return gsas_file_name_dict


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


def save_vulcan_gss(input_workspace, binning_parameter_dict, output_file_name, ipts, gsas_param_file):
    """

    :param input_workspace:
    :param binning_parameter_dict:
    :param output_file_name:
    :param ipts:
    :param gsas_param_file:
    :return:
    """
    # save to a general GSAS files and load back for the data portion
    bank_buffer_dict = dict()

    for binning_parameters in binning_parameter_dict:
        # save GSAS to single bank temporary file
        gsas_file_dict = save_gsas_temp(input_workspace, output_file_name, binning_parameters)

        # load the GSAS file and convert the header
        bank_id_list = binning_parameter_dict[binning_parameters]
        for bank_id in bank_id_list:
            gsas_file_buffer = read_gsas_file(gsas_file_dict[bank_id])
            bank_buffer_dict[bank_id] = gsas_file_buffer
        # END-FOR
    # END-FOR (binning_parameters)

    # form final output buffer
    vulcan_gss_buffer = ''

    header = generate_vulcan_gda_header(input_workspace, gsas_file_name=output_file_name, ipts=ipts,
                                        gsas_param_file_name=gsas_param_file)
    vulcan_gss_buffer += header

    for bank_id in sorted(bank_buffer_dict.keys()):
        vulcan_gss_buffer += bank_buffer_dict[bank_id]

    # save GSAS file
    try:
        gsas_file = open(output_file_name, 'w')
        gsas_file.write(vulcan_gss_buffer)
        gsas_file.close()
    except OSError as os_err:
        raise RuntimeError('Unable to write to {0} due to {1}'.format(output_file_name, os_err))

    return







