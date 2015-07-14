Feature: Wenduo Zhou
	I wish to demonstrate 
	How PyVDrive is used to reduce Vulcan data

	Background: 
		Given I am using PyVDrive

	Scenario: Reduce data in one run of VULCAN
		Given I input IPTS, run number, calibration file name and etc
		# IPTS = 10311  Run = [57070, 57078]
		Then I reduce the data
		# /SNS/VULCAN/shared/autoreduce/vulcan_foc_all_2bank_11p.cal
		Then I should see a matrix workspace generated
