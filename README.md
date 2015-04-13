# PyVDrive
A data reduction and analysis software for (SNS) VULCAN based on PyQt.


Use cases
* Use case: Load a reduce VULCAN data 
  a) Launch VDrivePlot;
  b) Create a new project;
  c) New 'Reduction setup' window;
  d) In 'reduction setup' window, select *Project*
  e) 'Browse' vanadium database file 
    (x)  upgrade 1: if *vanadium data base file* is a valid file name, there is no need to show the *file dialog box* again;
  >  upgrade 2: use a config file to pre-select some log names for matching;
  f) PushButton 'Add' to add IPTS/runs to pool for reduction;
  >  upgrade 1: pop out a window to show the matched vanadium runs for all the added runs for future setup;
  g) Set up bin size
  h) Reduce!


Next: 
1. Use case to add data:
  1) User gives an IPTS number;
  2) User says 'Add';
  3) VDrivePlot scans all the runs under that IPTS;
  4) VDrivePlot matches the vanadium runs according to user's specification; and lists all the matched v-runs in an order.



