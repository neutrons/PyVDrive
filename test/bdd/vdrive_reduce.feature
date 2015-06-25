Feature: Wenduo Zhou
	I wish to demonstrate 
	How PyVDrive is used to reduce Vulcan data

	Background: 
		Given I am using PyVDrive

	Scenario: Reduce data in one run of VULCAN
		Given I input IPTS, run number, calibration file name and etc.
		Then I should see a matrix workspace generated
