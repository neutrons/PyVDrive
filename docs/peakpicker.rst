Peak Picker Window
------------------

This is the design document for peak picker window


Business Model
==============

Typical workflow
++++++++++++++++

A typical workflow is composed of a couple of steps
  1. User have PeakPickerWindow to load a GSAS data file;
  2. PeakPickerWindow plots the GSAS on canvas;
  3. User pushes the *Find Peaks* button so that PeakPickerWindow finds all peaks in automatic mode.
     The peaks that are found will be added to the table workspace with fitted parameters;
  4. User pushes the *Plot Fitted Peaks* button so that the fitted peaks are plot against the experimental data;
  5. User deletes some peaks that are not well defined;
  6. User add some peaks that are not found by automatic algorithm.


Features of interactive plotting
++++++++++++++++++++++++++++++++

Peak-picker window provides user with interactive plotting to work with diffraction peaks.
Here are some operations that will be supported.

  - Set a vertical (indictor) line to indicate a peak;
  - Highlight a peak or a region of the diffraction pattern and undo the highlighting operation;
  - Plot the model of a peak (i.e., fitted peak) and the difference to experimental data;
  - Select the peak range and/or peak width.


Technical Model
===============

This section introduces how to map the user required features to program.

DiffracitonPlotView
+++++++++++++++++++

DiffractionPlotView: 
   It is an extension to MplCanvas such that it provides users with interactive plot
