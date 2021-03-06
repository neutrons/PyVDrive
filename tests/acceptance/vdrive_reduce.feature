Feature: Wenduo Zhou
	I wish to demonstrate 
	How VDriveAPI is used to reduce Vulcan data

	Background: 
		Given I am using VDriveAPI

	Scenario: Reduce data in one run of VULCAN
		Given I get a list of runs belonged to an IPTS number
	  	Then I filter the runs by date
		Then I input IPTS, run numbers
  	   	Then I save current session to a file
  		Then I create a new VDriveAPI project and load saved session file to it
  		Then I add add a run number to the VDrive project for reduction
  		Then I reduce the data
  		Then I check a matrix workspace generated from that run
		# IPTS = 10311  Run = [57070, 57078]
        #Then I input names of calibration file name and etc
		#Then I reduce the data
		# /SNS/VULCAN/shared/autoreduce/vulcan_foc_all_2bank_11p.cal
		#Then I should see a matrix workspace generated
