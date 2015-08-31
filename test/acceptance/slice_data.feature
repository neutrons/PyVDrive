Feature: Wenduo Zhou
	I wish to demonstrate 
	How VDriveAPI is used to slice Vulcan data

	Background: 
		Given I am using VDriveAPI

	Scenario: Reduce data in one run of VULCAN
 		Given I get a list of runs from a local directory
	  	Then I filter the runs by run numbers
		Then I input run number
  	   	Then I save current session to a file
  		Then I create a new VDriveAPI project and load saved session file to it
  		Then I input name of a sample log to get its data


