# this is supposed to run inside Mantid

# [SECTION OF VANADIUM]
# Load vanadium
Load(Filename='/SNS/VULCAN/IPTS-22752/nexus/VULCAN_172254.nxs.h5', OutputWorkspace='van')

# save for counts
ConvertToMatrixWorkspace(InputWorkspace='van', OutputWorkspace='van_sum')
CreateSingleValuedWorkspace(OutputWorkspace='__python_binary_op_single_value', DataValue=1)  # avoid zero count spec
Plus(LHSWorkspace='van_sum', RHSWorkspace='__python_binary_op_single_value', OutputWorkspace='van_sum')
# Transpose(InputWorkspace='van_sum', OutputWorkspace='van_sum')   Disabled for not writing out
# total counts of high angle bank
ha_counts = SumSpectra(InputWorkspace='van_sum', OutputWorkspace='high_angle', StartWorkspaceIndex=6467)
high_angle_bank_van_counts = ha_counts.readY(0)[0]
print ('High angle bank total counts = {}'.format(high_angle_bank_van_counts))


# convert to wave length, rebin
ConvertUnits(InputWorkspace='van', OutputWorkspace='van', Target='Wavelength')
Rebin(InputWorkspace='van', OutputWorkspace='van', Params='-0.001')   # -0.01 is too raw
SumSpectra(InputWorkspace='van', OutputWorkspace='van_sum_lambda_high_angle', StartWorkspaceIndex=6467)
FFTSmooth(InputWorkspace='van_sum_lambda_high_angle', OutputWorkspace='smooth2', Filter='Butterworth', Params='5,10', IgnoreXBins=True)


"""
# [SECTION TO NORMALIZE SINGLE CRYSTAL EXPERIMENT]
Load(Filename='/SNS/VULCAN/IPTS-22132/nexus/VULCAN_172240.nxs.h5', OutputWorkspace='Single_172240')
# convert to wave length, rebin and normalized by smooth vanadium
ConvertUnits(InputWorkspace='Single_172240', OutputWorkspace='Single_172240', Target='Wavelength')
Rebin(InputWorkspace='Single_172240', OutputWorkspace='Single_172240', Params='-0.001')
Divide(LHSWorkspace='Single_172240', RHSWorkspace='smooth2', OutputWorkspace='Single_172240_Norm')
# Convert to dSpacing
ConvertUnits(InputWorkspace='Single_172240_Norm', OutputWorkspace='Single_172240_Norm', Target='dSpacing')
# Divide by counts per pixels
final = Divide(LHSWorkspace='Single_172240_Norm', RHSWorkspace='van_sum', OutputWorkspace='Single_172240_Norm')
# multiply by total counts
final *= high_angle_bank_van_counts
"""

# [SECTION TO NORMALIZE SINGLE CRYSTAL EXPERIMENT]
Load(Filename='/SNS/VULCAN/IPTS-22752/nexus/VULCAN_172254.nxs.h5', OutputWorkspace='Single_172240')
# convert to wave length, rebin and normalized by smooth vanadium
ConvertUnits(InputWorkspace='Single_172240', OutputWorkspace='Single_172240', Target='Wavelength')
Rebin(InputWorkspace='Single_172240', OutputWorkspace='Single_172240', Params='-0.001')
Divide(LHSWorkspace='Single_172240', RHSWorkspace='smooth2', OutputWorkspace='Single_172240_Norm')
# Convert to dSpacing
ConvertUnits(InputWorkspace='Single_172240_Norm', OutputWorkspace='Single_172240_Norm', Target='dSpacing')
# Divide by counts per pixels
final = Divide(LHSWorkspace='Single_172240_Norm', RHSWorkspace='van_sum', OutputWorkspace='Single_172240_Norm')
# multiply by total counts
final *= high_angle_bank_van_counts



# Transpose(InputWorkspace='van_sum', OutputWorkspace='van_sum')
# CreateSingleValuedWorkspace(OutputWorkspace='__python_binary_op_single_value', DataValue=1)
# Plus(LHSWorkspace='van_sum', RHSWorkspace='__python_binary_op_single_value', OutputWorkspace='van_sum')
# Divide(LHSWorkspace='single_norm', RHSWorkspace='van_sum', OutputWorkspace='single_norm')
# Rebin(InputWorkspace='single_norm', OutputWorkspace='single_norm', Params='-0.001')
# Rebin(InputWorkspace='single_norm', OutputWorkspace='single_norm_s', Params='0.4,-0.001,3.5', PreserveEvents=False, FullBinsOnly=True, IgnoreBinErrors=True)
# SumSpectra(InputWorkspace='single_norm_s', OutputWorkspace='single_norm_s', StartWorkspaceIndex=6467)



