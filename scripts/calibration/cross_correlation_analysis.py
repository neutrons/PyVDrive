# This is the main cross correlation code. It is supposed to run with inside MantidPlot
# 
import mantid
import cross_correlation_lib as cross_correlation
import os

# Analyze the result from cross-correlation
# (This is intended to be used with Mantid or IPython Notebook)

# Step 1: Prepare: load, rebin, convert units from the raw event NeXus data
if 0:
    # 2017 Startup
    working_dir = '/SNS/users/wzz/Projects/VULCAN/nED_Calibration/Diamond_NeXus/'
    nxs_file_name = os.path.join(working_dir, 'VULCAN_150178_HighResolution_Diamond.nxs')
if 0:
    # 2018 Summer
    nxs_file_name = '/SNS/VULCAN/IPTS-21356/nexus/VULCAN_161364.nxs.h5'
    # prepare!
    Load(Filename='/SNS/VULCAN/IPTS-21356/nexus/VULCAN_161364.nxs.h5', OutputWorkspace='vulcan_diamond')
    ConvertUnits(InputWorkspace='vulcan_diamond', OutputWorkspace='vulcan_diamond', Target='dSpacing')
    Rebin(InputWorkspace='vulcan_diamond', OutputWorkspace='vulcan_diamond', Params='0.5,-0.0003,3')
    ConvertToMatrixWorkspace(InputWorkspace='vulcan_diamond', OutputWorkspace='vulcan_diamond_matrix')
    SaveNexusProcessed(InputWorkspace='vulcan_diamond_matrix',
            Filename='/SNS/users/wzz/Projects/VULCAN/20180411_Calibration/VULCAN_Diamond_Matrix.nxs', Title='Diamond for instrument geometry calibration')
if 0:
    # 2018 August
    nxs_file_name = '/SNS/VULCAN/IPTS-21356/nexus/VULCAN_164960.nxs.h5'
    # load data and convert units and rebin
    # Load(Filename='/SNS/VULCAN/IPTS-21356/nexus/VULCAN_161364.nxs.h5', OutputWorkspace='vulcan_diamond')
    # ConvertUnits(InputWorkspace='vulcan_diamond', OutputWorkspace='vulcan_diamond', Target='dSpacing')
    Rebin(InputWorkspace='vulcan_diamond', OutputWorkspace='vulcan_diamond', Params='0.5,-0.0003,3')
    # Convert to matrix workspace to save memory
    ConvertToMatrixWorkspace(InputWorkspace='vulcan_diamond', OutputWorkspace='vulcan_diamond_matrix')
    # 
    SaveNexusProcessed(InputWorkspace='vulcan_diamond_matrix',
            Filename='/SNS/VULCAN/shared/CALIBRATION/2018_9_10_CAL/calibration_data/VULCAN_Diamond_Matrix.nxs', Title='Diamond for instrument geometry calibration')

    
# Step 2: Prepare for the workspace name and etc
if True:
    nxs_file_name = '/SNS/users/wzz/Projects/VULCAN/Calibration_20180530/VULCAN_161364_diamond.nxs'
    nxs_file_name = '/SNS/VULCAN/shared/CALIBRATION/2018_9_10_CAL/calibration_data/VULCAN_Diamond_Matrix.nxs'

    # decide to load or not and thus group workspace
    diamond_ws_name, group_ws_name = cross_correlation.initialize_calibration(nxs_file_name, False)


if True:
    # 3 bank: west, east, high angle

    # do cross-correlation with 1 fit
    calib_ws_1fit_dict, mask_ws_1fit_dict =\
        cross_correlation.cross_correlate_vulcan_data(diamond_ws_name, group_ws_name, fit_time=1, flag='1fit')
    
    # do cross-correlation with 2 fit
    calib_ws_2fit_dict, mask_ws_2fit_dict =\
        cross_correlation.cross_correlate_vulcan_data(diamond_ws_name, group_ws_name, fit_time=2, flag='2fit')

    bank_name_list = ['west', 'east', 'high angle']

elif Flase:
    # 2 bank: west/east, high angle
    # do cross-correlation with 1 fit
    calib_ws_1fit_dict, mask_ws_1fit_dict =\
        cross_correlation.cross_correlate_vulcan_data_2bank(diamond_ws_name, group_ws_name, fit_time=1, flag='1fit')
    
    # do cross-correlation with 2 fit
    calib_ws_2fit_dict, mask_ws_2fit_dict =\
        cross_correlation.cross_correlate_vulcan_data_2bank(diamond_ws_name, group_ws_name, fit_time=2, flag='2fit')
    
    bank_name_list = ['westeast', 'high angle']

else:
    print ('DOING NOTHING ... QUIT!')
    sys.exit(1)

# compare the masked workspace
for bank_name in bank_name_list:
    mask_1fit_ws = mask_ws_1fit_dict[bank_name]
    masked_1fit_ws_indexes = cross_correlation.get_masked_ws_indexes(mask_1fit_ws)
    mask_2fit_ws = mask_ws_2fit_dict[bank_name]
    masked_2fit_ws_indexes = cross_correlation.get_masked_ws_indexes(mask_2fit_ws)

    # get the difference
    print ('Bank: {0}'.format(bank_name.upper()))
    print ('1-Fit: Number of masked spectra = {0};   2-Fit: Number of masked spectra = {1}'\
              ''.format(len(masked_1fit_ws_indexes ), len(masked_2fit_ws_indexes)))

    diff_spectra_set = set(masked_2fit_ws_indexes) - set(masked_1fit_ws_indexes)
    diff_spectra_set_op = set(masked_1fit_ws_indexes) - set(masked_2fit_ws_indexes)

    print ('Masked pixels set difference: {0} vs {1}'.format(len(diff_spectra_set), len(diff_spectra_set_op)))

    ofile = open('diff_mask_{0}.txt'.format(bank_name), 'w')
    ofile.write('{0}\n'.format(list(diff_spectra_set)))
    ofile.write('{0}\n'.format(list(diff_spectra_set_op)))
    ofile.close()

# check the counts of the differently masked workspace


# investigate the masked spectra from highest counts


# plot the compared cross-correlated peaks in the background and export to PNGs
