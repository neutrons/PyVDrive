#!/usr/bin/python
# Test pyvdrive.lib.vulcan_slice_reduce.SliceFocusVulcan
import pyvdrive.lib.vulcan_slice_reduce as vulcan_slice_reduce


def test_vanadium():
    """
    test main
    :return:
    """
    reducer = vulcan_slice_reduce.SliceFocusVulcan(number_banks=7)
    reducer.load_detector_eff_file(file_name='')
    ref_id = reducer.load_data()
    reducer.align_data(ref_id)
    reducer.apply_detector_efficiency(compress=True)
    reducer.diff_focus(ref_id, unit='d', binning='-0.0004')
    reducer.save_nexus(ref_id, out_file='blabla.nxs')

    print (reducer)

if __name__ == '__main__':
    test_vanadium()
