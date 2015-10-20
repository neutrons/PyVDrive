Feature: Wenduo Zhou
	I wish to demonstrate 
	How VDriveAPI is used to slice Vulcan data

	Background: 
		Given I am using VDriveAPI

	Scenario: Reduce data in one run of VULCAN
 		Given I get a list of runs from a local directory
	  	Then I filter the runs by run numbers
		Then I input run number
  		Then I input name of a sample log to get its data
	  	Then I set up rules to slice this run by this sample log and generate data slicer
		Then I slice data and check result
#
#	    Then I set up rules to slice this run by time
#	    Then I have data sliced by previous setup and check result
#	    Then I set up a list of time segments to generate data slicer
#	    Then I apply the data slicer to a run and check the result
