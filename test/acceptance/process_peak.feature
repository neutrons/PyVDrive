Feature: Wenduo Zhou
	I wish to test the workflow to calcualte reflections of 
	a given crystal structure with unit cell size.

	Background: 
		Given I am using mantid helper

	Scenario: Calculate reflections of silicon in d-spacing
 		Given I know the IPTS number and run number of a run for silicon
	  	Then I input the lattice parameters of silicon and calculate the reflections in d spacing
	    Then I reduce a silicon run

