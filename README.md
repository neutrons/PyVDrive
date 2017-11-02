# PyVDrive

A data reduction and analysis software for (SNS) VULCAN based on PyQt.



Format of Files
---------------

Time segment file
=================

The format of the time segment file for data slicing is compose of two parts.

The first part is the comment lines started with *#*.  
Two parameters have been defined.  
They are *Reference Run Number* and *Run Start Time*. 

The second part is for time segment. 
Each row must contain start and stop time for a time segment.
The third item is optional to be the target workspace's ID. 
Two adjacent item must be separated by tab.

Example:
 # Ignored information
 # Reference Run Number = 12345
 # Run Start Time = 9999999.99999999
 # Ignore information
 t0	t1	1
 t2	t3	2




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

* Use case: Reduce VULCAN data with VDrivePlot (Beta) without data slicing

 1. Launch VDrivePlot (beta);
 2. Click button **Select IPTS folders**
 3. The IPTS number with its children run numbers will be shown in a tree view
 4. User wills specify calibration file by either via button **Calibration files* or editor for run number.
 5. User selects sample environment with three options
  - VULCAN loadframe
  - Generic DAQ
  - User log file
 6. User chooses **VULCAN loadframe**
 7. User inputs first run and last run in the *sequential* tab;
 8. In tab *CHOP*, user specifies the amount of time to be skipped from the beginning of the algorithm;
 9. User checks checkbox ** Just chop neutron data** in order not to synchronize with log data (loadframe, DAQ, and etc.)
 10. User checks checkbox **Chop continuously over runs**;
  - without this option, the output files will be i/file1, i/file2, ..., j/file1, j/file2, ... for run i, j and k
  - with this option, the result will be recorded in i/file1, i/file2, ...., i/fileN
 11. User checks checkbox **Connect runs**, which will chop runs i, j and k, and remove the time lag between any consecutive runs
 12. User chooses data-chopping scheme as 'By picked segments' in two options
  - By constant intervals or
  - By picked segments
 13. Push button **Load time segment** is thus enabled;
 14. User pushes button **Load time segment** to load the time segment file;
 15. The name of the loaded segmentation file will be shown on
 16.



* Use case: Slice event data among multiple runs



* Use case: Modify configuration
 1. In Menu bar, click **Tools/Configuration**;
 2. A configuration window is thus popped out;
 3. Change the setup in configuration window;
 4. Click button **Verify**;
 5. If some setup is not allowed, a warning dialog is popped out;
 6. Click button **Save**;
 7. Alternatively, click button **Save As** to save configuration file to another file other than **~/.vdrive/config**;



PyVDrive Features
-----------------

Configuration
=============

Configuration file is search automatically under * ~/.vdrve/config * under Linux/MacOS or *C:\.vdrive\config*;

A customized configuration file can be loaded as an option;

Calibration
===========

Pair:
 -rw-rwxr-- 1 13489 49133 403704 Jun 16 16:43 70487-s.gda
 -rw-rwxr-- 1 13489 49133   3240 Jun 16 16:43 Vulcan-70487-s.prm


Time segment file
=================

A test/xml file that contains the segments of time for slicing;

The time segments are either in relative time to the run start time or absolute time from 1990.01.01:00:00:00


Deprecated use cases
--------------------

* Use case: Reduce VUCLAN data with VDrivePlot_Alpha (This use case will be removed after VDrivePlot_Beta is implemented)
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
  
  
  
Reduction
---------

Process vanadium run
====================

 1. Compress events;
 2. SetSampleMaterial;
 3. MultipleScatteringCylinderAbsorption;
 4. Align and focus;
 5. StripVanadiumPeaks;
 6. FFTSmooth;
 7. SetUncertainties;




Features
--------

Here is a detailed introduction on features that have been implemented. 

Configuration
=============

Configuration is a *python* module to load from current working directory. 
It is loaded and managed by a VDriveAPI object instantiated in either
*VDrivePlot* or test scripts. 

The order of loading configuration is 
 * PyVDrive.config 
 * 




New Features
------------

(X) Set up a configuration file for VDrive!

(X) Create a class named 'VDriveConfig' (Empty)
  * Instread: VDriveAPI._myConfigObj  (_)

3. Load the selected VDrive logs to match in config





