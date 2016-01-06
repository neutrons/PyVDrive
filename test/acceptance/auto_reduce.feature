Feature: Wenduo Zhou
	I wish to prove that PyVdrive can reduce data
    same as auto reduction script.

	Background: 
		Given I am using VDriveAPI

	Scenario: Reduce data in one run of VULCAN
		Given I get one run belonged to an IPTS number
	  	Then I create a reduction project
		Then I set the IPTS number and get runs from its archive
	    Then I add just a few runs
		Then I check IPTS and run numbers from the workflow instance
  		Then I add a run number to the VDrive project for reduction
  		Then I reduce the specified Vulcan run
  		Then I export the reduced data to GSAS file
		# IPTS = 10311  Run = [57070, 57078]
        #Then I input names of calibration file name and etc
		#Then I reduce the data
		# /SNS/VULCAN/shared/autoreduce/vulcan_foc_all_2bank_11p.cal
		#Then I should see a matrix workspace generated
