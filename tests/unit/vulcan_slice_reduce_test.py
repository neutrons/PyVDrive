#!/usr/bin/python
# Test pyvdrive.lib.vulcan_slice_reduce.SliceFocusVulcan
import pyvdrive.lib.vulcan_slice_reduce as vulcan_slice_reduce


def test_vanadium():
    """
    test main
    :return:
    """
    reducer = vulcan_slice_reduce.SliceFocusVulcan(number_banks=7)
    reducer.load_detector_eff_file(file_name='tests/data/vulcan_eff_156473.hdf5')
    event_file_name = '/SNS/VULCAN/IPTS-19576/nexus/VULCAN_{0}.nxs.h5'.format(156473)
    ref_id = reducer.load_data(event_file_name=event_file_name)
    reducer.align_detectors(ref_id)
    reducer.diffraction_focus(ref_id, unit='d', binning='-0.0004', apply_det_efficiency=True)
    reducer.save_nexus(ref_id, output_file_name='vulcan_det_eff_27banks.nxs')

    reducer = vulcan_slice_reduce.SliceFocusVulcan(number_banks=27)
    event_file_name = '/SNS/VULCAN/IPTS-19576/nexus/VULCAN_{0}.nxs.h5'.format(156473)
    ref_id = reducer.load_data(event_file_name=event_file_name)
    reducer.align_detectors(ref_id)
    reducer.diffraction_focus(ref_id, unit='d', binning='-0.0004', apply_det_efficiency=False)
    reducer.save_nexus(ref_id, output_file_name='vulcan_raw_27banks.nxs')

    print (reducer)

if __name__ == '__main__':
    test_vanadium()
