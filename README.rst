TODO List
---------

1. Test mask detectors with get detectors in same rows or in same columns

2. Refactor the Mantid reduction hierarchy for PyVDrive-Vulcan-Reduction 2.0
  a) goal 1: replace SNSPowderReduciton
  b) goal 2: unify the reduction workflow for single run reduction and chopped run reduction
  c) target code structure
    i.   API: bridge between UI and library
    ii.  Project manager: placeholder for ReductionManager
    iii. Reduction manager: placeholder of data file, raw workspace and reduced workspace, reduction states
    iv.  mantid_reduction: wrapper on Mantid reduction algorithms


Glossary:
1. Reduction: align and focus powder optionally with filtering bad pulses and etc


IDL-VDRIVE Binning
------------------

**CalibrationManager** is responsible to load and manage all the binning references for output to GSAS.
The problem may well be tackled when Mantid is able to Rebin workspaces with various binnig parameters on various spectra.

*VDRIVE Binning Refernece* will be dated synchronized with calibration file's date.
This is not an efficient solution in terms of memory.
But it is simpler in programming.

Regular binning with option to data slicing
===========================================

Run's *run\_start* is used to identify the calibration file suite, including calibration file and VDRIVE GSAS binning template file.

Processing Vanadium
===================

1. Bin dSpacing to default 0.001 and 0.0003 for various banks
2. Remove vanadium peaks
3. Convert unit to TOF
4. Rebin to VDRIVE-GSAS bins
5. Smooth
6. Merge
7. Call SaveGSS()
