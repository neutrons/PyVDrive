# TODO FIXME NOW3 Implement
import mantid
import cross_correlation
import os

# Analyze the result from cross-correlation
# (This is intended to be used with Mantid or IPython Notebook)

# prepare
working_dir = '/SNS/users/wzz/Projects/VULCAN/nED_Calibration/Diamond_NeXus/'
nxs_file_name = os.path.join(working_dir, 'VULCAN_150178_HighResolution_Diamond.nxs')

# decide to load or not and thus group workspace
diamond_ws_name, group_ws_name = cross_correlation.initialize_calibration(nxs_file_name, False)

# do cross-correlation with 1 fit
calib_ws_1fit_dict, mask_ws_1fit_dict =\
    cross_correlation.cross_correlate_vulcan_data(diamond_ws_name, group_ws_name, fit_time=1, flag='1fit')

# do cross-correlation with 2 fit
calib_ws_2fit_dict, mask_ws_2fit_dict =\
    cross_correlation.cross_correlate_vulcan_data(diamond_ws_name, group_ws_name, fit_time=2, flag='2fit')

# compare the masked workspace
for bank_name in ['west', 'east', 'high angle']:
    mask_1fit_ws = mask_ws_1fit_dict[bank_name]
    masked_1fit_ws_indexes = cross_correlation.get_masked_ws_indexes(mask_1fit_ws)
    mask_2fit_ws = mask_ws_2fit_dict[bank_name]
    masked_2fit_ws_indexes = cross_correlation.get_masked_ws_indexes(mask_2fit_ws)

    # get the difference
    print ('Bank: {0}'.format(bank_name.upper()))
    print ('1-Fit: Number of masked spectra = {0};   2-Fit: Number of masked spectra = {1}'.format(len(masked_1fit_ws_indexes ), len(masked_2fit_ws_indexes)))

    diff_spectra_set = set(masked_2fit_ws_indexes) - set(masked_1fit_ws_indexes)
    diff_spectra_set_op = set(masked_1fit_ws_indexes) - set(masked_2fit_ws_indexes)

    print ('Difference: {0} vs {1}'.format(len(diff_spectra_set), len(diff_spectra_set_op)))

    ofile = open('diff_mask_{0}.txt'.format(bank_name), 'w')
    ofile.write('{0}\n'.format(list(diff_spectra_set)))
    ofile.write('{0}\n'.format(list(diff_spectra_set_op)))
    ofile.close()

# check the counts of the differently masked workspace


# investigate the masked spectra from highest counts


# plot the compared cross-correlated peaks in the background and export to PNGs
