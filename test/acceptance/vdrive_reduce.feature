Feature: Wenduo Zhou
	I wish to demonstrate 
	How VDriveAPI is used to reduce Vulcan data

	Background: 
		Given I am using VDriveAPI

	Scenario: Reduce data in one run of VULCAN
		Given I get a list of runs from a local directory
	  	Then I filter the runs by run numbers
		Then I input run number
  	   	Then I save current session to a file
  		Then I create a new VDriveAPI project and load saved session file to it
  		Then I input a sample log's name to get its data
		# IPTS = 10311  Run = [57070, 57078]
        #Then I input names of calibration file name and etc
		#Then I reduce the data
		# /SNS/VULCAN/shared/autoreduce/vulcan_foc_all_2bank_11p.cal
		#Then I should see a matrix workspace generated
