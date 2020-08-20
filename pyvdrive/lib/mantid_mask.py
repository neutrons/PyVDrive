# Module contains a set of static methods to mask detectors as ROI and/mask
import mantid_helper
import datatypeutility


class MantidMaskingManager(object):
    """
    A workspace management and operation class for masking workspace (for Mask and ROI) in Mantid
    """

    def __init__(self):
        """
        initialization
        """
        # dictionary to map masking/
        self._mask_file_ws_dict = dict()

        return

    def load_mask_xml(self, mask_file_name, ref_ws_name, is_roi):
        """
        load a mask in Mantid XML format
        :param mask_file_name:
        :param ref_ws_name:
        :param is_roi: flag that the mask is a ROI
        :return:
        """
        datatypeutility.check_file_name(mask_file_name, check_exist=True, check_writable=False,
                                        is_dir=False, note='Mask/ROI (Mantiod) XML file')

        if mask_file_name in self._mask_file_ws_dict:
            # previously loaded
            mask_ws_name, is_roi = self._mask_file_ws_dict[mask_file_name]
        else:
            # create workspace name as the standard
            mask_ws_name = mask_file_name.lower().split('.xml')[0].replace('/', '.')
            # load
            if is_roi:
                mask_ws_name = 'roi.' + mask_ws_name
                mantid_helper.load_roi_xml(ref_ws_name, mask_file_name, mask_ws_name)
            else:
                mask_ws_name = 'mask.' + mask_ws_name
                mantid_helper.load_mask_xml(ref_ws_name, mask_file_name, mask_ws_name)

            # record
            self._mask_file_ws_dict[mask_file_name] = mask_ws_name, is_roi
        # END-IF-ELSE

        return mask_ws_name

    def mask_detectors(self, ws_name, roi_file_list, mask_file_list):
        """
        mask detectors by ROI and/or mask
        :param ws_name:
        :param roi_file_list:
        :param mask_file_list:
        :return: workspace reference
        """
        # check inputs
        datatypeutility.check_string_variable('Workspace name', ws_name)

        datatypeutility.check_list('ROI file names', roi_file_list)
        datatypeutility.check_list('Mask file names', mask_file_list)

        # return if nothing to do
        if len(roi_file_list) + len(mask_file_list) == 0:
            matrix_ws = mantid_helper.retrieve_workspace(ws_name, raise_if_not_exist=True)
            return matrix_ws

        # load mask file and roi file
        roi_ws_list = list()
        mask_ws_list = list()

        for roi_file in roi_file_list:
            roi_ws_name_i = self.load_mask_xml(roi_file, ws_name, is_roi=True)
            roi_ws_list.append(roi_ws_name_i)
        for mask_file in mask_file_list:
            mask_ws_name_i = self.load_mask_xml(mask_file, ws_name, is_roi=False)
            mask_ws_list.append(mask_ws_name_i)

        # mask by ROI workspaces
        self.mask_detectors_by_rois(ws_name, roi_ws_list)
        # mask by masks workspace
        self.mask_detectors_by_masks(ws_name, mask_ws_list)

        matrix_ws = mantid_helper.retrieve_workspace(ws_name, raise_if_not_exist=True)

        return matrix_ws

    @staticmethod
    def mask_detectors_by_rois(ws_name, roi_ws_list):
        """
        mask detectors by ROIs
        :param ws_name:
        :param roi_ws_list:
        :return:
        """
        if len(roi_ws_list) == 1:
            # single mask workspace of ROI
            mantid_helper.mask_workspace(ws_name, roi_ws_list[0])
        else:
            # multiple mask workspaces of ROI
            raise NotImplementedError(
                'It need to be prototyped for how to combine (OR) for multiple mask workspaces')

        return

    @staticmethod
    def mask_detectors_by_masks(ws_name, mask_ws_list):
        """
        mask detectors by mask workspace one by one
        :param ws_name:
        :param mask_ws_list:
        :return:
        """
        for mask_ws_name in mask_ws_list:
            # Mask detectors
            mantid_helper.mask_workspace(to_mask_workspace_name=ws_name,
                                         mask_workspace_name=mask_ws_name)
        # END-FOR

        return
