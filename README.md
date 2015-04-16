# PyVDrive

A data reduction and analysis software for (SNS) VULCAN based on PyQt.

New Requests
------------

1. New project need a default name;
2. Provide *hint* to user;
3. If user gives **IPTS** as project name, then add all files to in that IPTS to project;
4. Give user hint to add another IPTS to the project 
5. Give user to define *filter* to load run, such as 
 * key word: *alignment*;
 * file size;
 * refer to AutoRecord.txt;
6. Reduced scope of vanadium run matching. 
 * Example: /SNS/VULCAN/IPTS-13587/shared/Instrument/ only *64927-s.gda* exists;
7. Add a separate window for viewing the reduced data
8. Add tag to output GSAS file: 'normalized by current', 'normalized by vanadium', ...


Use cases
---------

VDrive is an application that is driven by use cases.

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


 
* Use case to add data:
  1) User gives an IPTS number;
  2) User says 'Add';
  3) VDrivePlot scans all the runs under that IPTS;
  4) VDrivePlot matches the vanadium runs according to user's specification; and lists all the matched v-runs in an order.



Features
--------

Here is a detailed introduction on features that have been implemented. 

Configuration
=============

Configuration is a module to load from current working directory. 
It is loaded and managed by a VDriveAPI object instantiated in either
*VDrivePlot* or test scripts. 

If the current working directory does not have configuration file, then
it will be recorded from ~/.vdrive/config.py



New Features
------------

(X) Set up a configuration file for VDrive!

(X) Create a class named 'VDriveConfig' (Empty)
  * Instread: VDriveAPI._myConfigObj  (_)

3. Load the selected VDrive logs to match in config



