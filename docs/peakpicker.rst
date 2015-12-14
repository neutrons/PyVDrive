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

Introduction of widgets in GUI
++++++++++++++++++++++++++++++

Here is the brief introduction to most of the widgets that are used.

- Push button **Read Data**: importing a set of GSAS data;
- Crystal structure group including **PhaseName**, **Structure** and etc.: ;
- Table **PeakParameter**: containing all peaks' parameters including bank number, name of the peak, 
  number of overlapped peaks in the range, peak centre (in-dsapcing), peak width (i.e., peak range as 6 times of FWHM). 

Operations to peaks
+++++++++++++++++++

For the peak parameters table,

- Each row of the table contains peak parameters for one individual diffraction peak;
  - bank number
  - name of peak
  - position
  - width
- Overlapped peaks will be grouped such that they can be written to output file properly;
- The width, i.e., peak range of overlapped peaks should range from the left side of the left-most peak
  and right side of the right-most peak.

Here is the list of operations that are supported for peak parameters' table.
- Merge several peaks to be the same entry in the output peak file by giving them the same peak name;
- Output to a peak file (peak.txt);
- Add a peak;
- Remove a peak;
- Load peaks from an existing peak file;


Features of interactive plotting
++++++++++++++++++++++++++++++++

Peak-picker window provides user with interactive plotting to work with diffraction peaks.
Here are some operations that will be supported.

- Set a vertical (indictor) line to indicate a peak;
- Highlight a peak or a region of the diffraction pattern and undo the highlighting operation;
- Plot the model of a peak (i.e., fitted peak) and the difference to experimental data;
- Select the peak range and/or peak width.


Output 1: Peak file
+++++++++++++++++++

The peak file is
- contains the peaks' information for single peak fitting by GSAS;
- a tab-spaced csv file;
 
An example can found at */SNS/VULCAN/IPTS-13859/shared/peak.txt*. 


Technical Model
===============

This section introduces how to map the user required features to program.

DiffracitonPlotView
+++++++++++++++++++

DiffractionPlotView: 
   It is an extension to MplCanvas such that it provides users with interactive plot
