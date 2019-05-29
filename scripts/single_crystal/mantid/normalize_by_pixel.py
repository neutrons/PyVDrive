# Task: Generate normalization factor/spectra from measured vanadium
# Date: 2019.05.29
# Version: 1.0
# Platform: MantidPlot
# Related script: (prev) generate_vanadium_normalization.py

# Pseudo-code/workflow
# pre-requisite:  vc_front, vc_back, [count_i]
# 1. load run
# 2. convert to wave length space and rebin
# 3. for each pixel:
#   (1) identify tube that it belongs to to determine front or back
#   (2) normalize by vc_front/vc_back and count_i
