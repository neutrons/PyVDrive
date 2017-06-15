# Methods to work with data binning for VDrivePlot
import gui.GuiUtility as GuiUtil


class VulcanGuiReduction(object):
    """
    A utility class to set up reduction/binning by gathering information from GUI.
    """
    def __init__(self, usr_interface, wf_controller):
        """
        initialization
        :param usr_interface:
        :param wf_controller:
        """
        # check
        assert usr_interface is not None, 'User interface object cannot be None.'
        assert wf_controller is not None, 'Controller instance cannot be None.'

        self.user_interface = usr_interface
        self.controller = wf_controller

        return

    def read_binning_parameters(self):
        """
        parse and check binning parameters.
        :return:
        """
        # parse binning parameter
        if self.user_interface.radioButton_binStandard.isChecked():
            # will use default binning parameter
            bin_par = None
        elif self.user_interface.radioButton_binCustomized.isChecked():
            # customized bin parameters
            bin_width = GuiUtil.parse_float(self.user_interface.lineEdit_binWidth)
            min_tof = GuiUtil.parse_float(self.user_interface.lineEdit_binMinTOF)
            max_tof = GuiUtil.parse_float(self.user_interface.lineEdit_binMaxTOF)
            bin_par = (min_tof, bin_width, max_tof)
        else:
            # violate requirements
            raise RuntimeError('It is impossible to have either standard binning or customized binning.'
                               'Will be implemented in #32.')

        return bin_par

    def read_pixel_binning_parameters(self):
        """
        binning pixel
        :return:
        """
        # return the case for not being checked
        if not self.user_interface.checkBox_overPixel.isChecked():
            return False, None

        # process the binning parameters
        if self.user_interface.radioButton_binVerticalPixels.isChecked():
            bin_pixel_size = GuiUtil.parse_integer(self.user_interface.lineEdit_pixelSizeVertical)
            bin_pixel_direction = 'vertical'
        elif self.user_interface.radioButton_binHorizontalPixels.isChecked():
            bin_pixel_size = GuiUtil.parse_integer(self.user_interface.lineEdit_pixelSizeHorizontal)
            bin_pixel_direction = 'horizontal'
        else:
            raise RuntimeError('Binning pixels: neither of 2 radio buttons (vertical/horizontal) is selected.')

        # form output
        par_dict = {'direction': bin_pixel_direction,
                    'pixel_size': bin_pixel_size}

        return True, par_dict

    def read_post_processing_options(self):
        """

        :return:
        """
        option_dict = dict()
        option_dict['background'] = self.user_interface.checkBox_reduceSubtractBackground.isChecked()
        option_dict['vanadium'] = self.user_interface.checkBox_reduceNormalizedByVanadium.isChecked()
        option_dict['special_pattern'] = self.user_interface.checkBox_reduceSubstractSpecialPattern.isChecked()

        return option_dict

    def read_output_options(self):
        """
        read the options for output from GUI.
        :return: dictionary
        """
        option_dict = dict()
        option_dict['auto_reduce'] = self.user_interface.checkBox_autoReduction.isChecked()
        option_dict['gsas'] = self.user_interface.checkBox_outGSAS.isChecked()
        option_dict['output_to_fullprof'] = self.user_interface.checkBox_outFullprof.isChecked()
        option_dict['record'] = self.user_interface.checkBox_outputAutoRecords.isChecked()
        option_dict['logs'] = self.user_interface.checkBox_outputSampleLogs.isChecked()
        option_dict['output_directory'] = str(self.user_interface.lineEdit_outputDir.text())

        return option_dict

    def read_run_number_list(self):
        """
        read the run numbers to reduce from GUI.
        :return:
        """
        # retrieve the runs to reduce
        run_number_list = self.user_interface.tableWidget_selectedRuns.get_selected_runs()
        if len(run_number_list) == 0:
            error_message = 'No run is selected in run number table.'
            return False, error_message

        return run_number_list

    def reduce_data(self):
        """
        main method to reduce data by gathering reduction options and parameters from GUI.
        :return:
        """
        # get the binning parameter
        bin_par = self.read_binning_parameters()

        # get run numbers to reduce
        run_number_list = self.read_run_number_list()

        # binning by pixel
        bin_by_pixel, pixel_option_dict = self.read_pixel_binning_parameters()

        # get output selection
        output_option_dict = self.read_output_options()

        # add runs to reduce
        status, error_message = self.controller.set_runs_to_reduce(run_numbers=run_number_list)
        if status is False:
            return False, error_message
            # GuiUtility.pop_dialog_error(self, error_message)

        arg_dict = {'binning_parameters': bin_par}
        arg_dict.update(output_option_dict)
        arg_dict['output_directory'] = self.controller.get_working_dir()

        if bin_by_pixel:
            # binning by pixel
            raise NotImplementedError('Binning by pixels is not implemented yet!')
        else:
            # regular binning
            print '[DB] GUI reducer setup: {0}.'.format(arg_dict)
            status, ret_obj = self.controller.reduce_data_set(**arg_dict)

        if status is False:
            error_msg = ret_obj
            return False, error_msg

        return True, None




