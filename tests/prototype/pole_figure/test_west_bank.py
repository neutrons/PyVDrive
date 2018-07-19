# This is a prototype test to verify the algorithm's correctness
import mantid.simpleapi as simple

# create a 5 spectra workspace
simple.CreateWorkspace(OutputWorkspace='vulcan_west_bank',
                       DataX='1,2,1,2,1,2,1,2,1,2',
                       DataY='2,2,2,2,2',
                       DataE='1,1,1,1,1',
                       NSpec=5,
                       UnitX='dSpacing')
# set up the instrument
simple.EditInstrumentGeometry(Workspace='vulcan_west_bank',
                              PrimaryFlightPath=43.753999999999998,
                              SpectrumIDs='1-5',
                              L2='2.04302,2.04302,2,2.04302,2.04302',
                              Polar='100.791,100.791,90,79.2093,79.2093',
                              Azimuthal='-4.75179,4.75179,0,-4.75179,4.75179',
                              DetectorIDs='1-5',
                              InstrumentName='VulcanWestBankOnly')

# import data
log_setup_file = open('vulcan_sample_log.txt', 'r')
lines = log_setup_file.readlines()
log_setup_file.close()

