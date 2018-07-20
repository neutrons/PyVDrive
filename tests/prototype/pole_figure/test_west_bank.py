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

hrot_omega_list = list()
for line in lines:
    line = line.strip()
    if len(line) == 0:
        continue
    elif line.startswith('#'):
        continue

    str_list = line.split()
    hrot = float(str_list[0])
    omega = float(str_list[1])

    hrot_omega_list.append((hrot, omega))
# END-FOR

# import pole figure
pole_figure_file = open('vulcan_sample_log.txt', 'r')
lines = log_setup_file.readlines()
log_setup_file.close()

pole_figure_list = list()
for line in lines:
    line = line.strip()
    if len(line) == 0:
        continue
    elif line.startswith('#'):
        continue

    str_list = line.split()
    r_td_list = list()
    r_nd_list = list()
    for i in range(5):
        r_td_list.append(float(str_list[2*i]))
        r_nd_list.append(float(str_list[2*i+1]))
    # END-FOR

    pole_figure_list.append((r_td_list, r_nd_list))
# END-FOR

# check against Mantid's algorithm
if len(hrot_omega_list) != len(pole_figure_list):
    raise RuntimeError('HROT/OMEGA list has a different size other than pole figure value list.  They are '
                       'not in 1-to-1 mapping')

num_tests = len(hrot_omega_list)

for itest in range(num_tests):
    # set up the instrument (test purpose)
    simple.AddSampleLog(Workspace='vulcan_west_bank', LogName='hrot_{0}'.format(itest),
                        LogText='{}'.format(hrot_omega_list[itest][0]),
                        LogType='Number Series')
    simple.AddSampleLog(Workspace='vulcan_west_bank', LogName='omega_{0}'.format(itest),
                        LogText='{}'.format(hrot_omega_list[itest][1]),
                        LogType='Number Series')

    # integration
    simple.Integration(InputWorkspace='vulcan_west_bank', OutputWorkspace='peak_intensity',
                       RangeLower=1.2, RangeUpper=1.8)

    # do conversion
    simple.ConvertToPoleFigure()

    # compare value
# END-FOR