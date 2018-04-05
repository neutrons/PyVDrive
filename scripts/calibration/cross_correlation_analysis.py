# TODO FIXME NOW3 Implement
import cross_correlation

# Analyze the result from cross-correlation
# (This is intended to be used with Mantid or IPython Notebook)

# prepare
nxs_file_name = 'VULCAN_150178_HighResolution_Diamond.nxs'

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



# check the counts of the differently masked workspace


# investigate the masked spectra from highest counts


# plot the compared cross-correlated peaks in the background and export to PNGs
