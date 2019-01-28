Cross-correlation calibration
-----------------------------

Used Diamond Runs
=================

Diamond_Runs = {'2017-06-01': '/SNS/users/wzz/Projects/VULCAN/nED_Calibration/Diamond_NeXus/'
                              'VULCAN_150178_HighResolution_Diamond.nxs',
                '2018-08-01': '/SNS/users/wzz/Projects/VULCAN/CalibrationInstrument/Calibration_20180910/'
                              'raw_dspace_hitogram.nxs'}


New Workflow
============

Prepare: Prepare from 'vulcan_calibration_template.sh'

Step 1: Generate matrix workspace for cross correlation. 

Step 2: Cross correlation (first round).

Step 3: Analyze the calibration file including (1) diffraction focus (2) report on masked spectra (counts, why failed, ...)

Step 4: Second-round cross correlation.

Step 5: Analyze the calibration file including (1) diffraction focus (2) compare the fit result and etc...


Library and User Scripts
========================

* cross_correlation_lib.py: main calibration library


Algorithms
==========

Calibration: Cross-correlation
++++++++++++++++++++++++++++++

Cross correlation with 2 round of peak fitting is used.


Correction
++++++++++

Calibrated DIFCs that are  .... ....






Outputs
=======

  * vulcan_20180412_calibration.h5
  * vulcan_2fit.cal
  * vulcan_2fit.h5
  * vulcan_vz_test.cal
  * vulcan_vz_test.h5



(Old) Workflow (MantidPlot based)
=================================

1. cross_correlation_analysis.py : do cross correlation, analyze the result and output calibration file
   cross_correlation_lib.py : library for cross-correlation

2. calculate_difc.py : calculate DIFC for raw and calibrated instrument

3. second round cross correlation

Auxiliary Codes
===============

* verify_reference_spectra.py
* calculate_difc.py
* create_test_data.py


== Task: Study the quality of cross-correlation ==

Q1: Is the masking generated from cross correlation reasonable? 

1. cross_correlation_analysis.py : main script to analyze the result of cross correlation
2. cross_correlation.py: main module to do all the cross-correlation related work
