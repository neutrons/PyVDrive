# Methods to work with data binning for VDrivePlot
import gui.GuiUtility as gutil


def do_bin_data(usr_interface, wf_controller):
    """ Brief: Bin a set of data
    Purpose:
        Reduce the event data to focused diffraction pattern.
        The process includes align, focus, rebin and calibration with vanadium.
    Requirements:
        At least 1 run is selected for reduce;
        calibration file for focusing is specified;
        ... ...
    Guarantees:
        Selected runs are reduced from event data to focused diffraction pattern
        good for Rietveld refinement.
        If the data slicing is selected, then reduce the sliced data.
    :return:
    """
    # Process data slicers
    # FIXME/TODO/NOW/
    if usr_interface.checkBox_chopRun.isChecked():
        raise NotImplementedError('Binning data with option to chop will be solved later!')

    # parse binning parameter
    if usr_interface.radioButton_binStandard.isChecked():
        # will use default binning parameter
        bin_par = None
    elif usr_interface.radioButton_binCustomized.isChecked():
        # customized bin parameters
        bin_width = gutil.parse_float(usr_interface.lineEdit_binWidth)
        min_tof = gutil.parse_float(usr_interface.lineEdit_binMinTOF)
        max_tof = gutil.parse_float(usr_interface.lineEdit_binMaxTOF)
        bin_par = (min_tof, bin_width, max_tof)
    else:
        # violate requirements
        raise RuntimeError('It is impossible to have either standard binning or customized binning.'
                           'Will be implemented in #32.')

    # bin over pixel
    # FIXME/TODO/FUTURE - Talk with Ke
    if usr_interface.checkBox_overPixel.isChecked():
        raise NotImplementedError('Binning over pixels shall be discussed with Ke.')
        # # binning pixel
        # bin_pixel_direction = ''
        # if usr_interface.radioButton_binVerticalPixels.isChecked():
        #     bin_pixel_size = GuiUtility.parse_integer(usr_interface.lineEdit_pixelSizeVertical)
        #     bin_pixel_direction = 'vertical'
        # elif usr_interface.radioButton_binHorizontalPixels.isChecked():
        #     bin_pixel_size = GuiUtility.parse_integer(usr_interface.lineEdit_pixelSizeHorizontal)
        #     bin_pixel_direction = 'horizontal'
        # else:
        #     GuiUtility.pop_dialog_error(self, 'Neither of 2 radio buttons is selected.')
        #     return
    # END-IF-ELSE

    # other parameters
    do_subtract_bkgd = usr_interface.checkBox_reduceSubtractBackground.isChecked()
    do_normalize_by_vanadium = usr_interface.checkBox_reduceNormalizedByVanadium.isChecked()
    do_substract_special_pattern = usr_interface.checkBox_reduceSubstractSpecialPattern.isChecked()
    do_write_fullprof = usr_interface.checkBox_outFullprof.isChecked()
    do_write_gsas = usr_interface.checkBox_outGSAS.isChecked()

    # Reduce data
    # retrieve the runs to reduce
    run_number_list = usr_interface.tableWidget_selectedRuns.get_selected_runs()
    if len(run_number_list) == 0:
        # gutil.pop_dialog_error(self, 'No run is selected in run number table.')
        error_message = 'No run is selected in run number table.'
        return False, error_message

    status, error_message = wf_controller.set_runs_to_reduce(run_numbers=run_number_list)
    if status is False:
        return False, error_message
        # GuiUtility.pop_dialog_error(self, error_message)

    arg_dict = {'bin_size': bin_par}

    status, ret_obj = wf_controller.reduce_data_set(**arg_dict)
    if status is False:
        error_msg = ret_obj
        return False, error_msg

    return True, None


