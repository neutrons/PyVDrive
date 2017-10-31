Descrption
----------

This is the document recording all the use cases. 
It serves as both the guideline of software development
and examples for users.


Use case: Simple data reduction
===============================

Simple data reduction

  1. User clicks button *Select IPTS folders*.  In the pop-up window, user selects an IPTS (*16053*) and a range of run numbers;
  2. **V-drive** checks and loads runs under IPTS to the project files tree (left most column);
  3. User selects one or multiple runs from the project tree, add them to the reduction list;
  4. In tab *VBIN*, user sets up the bin size and other reduction parameters;
  5. User clicks the *BIN DATA* button;
  6. **V-drive** reduces the selected runs;
  7. User may launch the *general plot* window to view the reduced data;
  8. User clicks the *Save* in the menu *File* to save the reduction result;


Use case: Single peak picking
=============================

PyVdrive provides the functionality to let user to pick up single peaks from reduced diffraction data
and thus generate input files for single peak fitting by GSAS.

  1. User obtains reduced diffraction data either via steps described in use case *simple data reduction* or by loading a previously saved project;
  2. In tab *???*, user launches the peak picking window;
  3. User may input the lattice parameters;
  4. User can either click button *Peak Finding*. If lattice parameters are given, then the peak finding will be based on the calculated peak positions from lattice parameters; otherwise, peak finding will be based on a special algorithm;
  5. ... ...




Use case: Determine slicing strategy
====================================
1. User selects a run (12345) from left-most tree;
2. User checks 'Chop data in column 2' and ... ;
3. User selects the raw data file and have the sample logs (meta
   data) loaded
4. VDrivePlot plots first 6 non-1-entry sample logs;
5. User picks one of the sample logs and sets up 
