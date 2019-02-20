# This is the main reduction script that is used by PyVDrive-Live
import mantid
from mantid.api import AnalysisDataService as ADS
import mantid.simpleapi as mantid

print '[DEBUG SNS] Mantid library is from {0}'.format(mantid)

# process live input workspace
counter_ws = ADS['_VULCAN_LIVE_COUNTER']
index = int(counter_ws.readX(0)[0])

ws = input
if ws.id() == 'EventWorkspace':
    num_events = input.getNumberEvents()
    print '[SNS-Live] Workspace {2} Iteration {0}: Number of events = {1}'.format(index, ws.getNumberEvents(), str(input))
else:
    num_events = -2
    print '[SNS-Live] Workspace {1} Iteration {0}: Not an EventWorkspace.'.format(index, str(input))


# stop processing if there is no events
if num_events > 10:
    # update counter
    counter_ws.dataX(0)[0] += 1
    counter_ws.dataY(0)[0] = num_events
    
    # reduce
    temp_ws_name = 'temp_{0}'.format(index)
    mantid.Rebin(InputWorkspace=input, OutputWorkspace=temp_ws_name, Params='5000., -0.001, 50000.')
    curr_ws_name = 'output_{0}'.format(index)
    mantid.AlignAndFocusPowder(InputWorkspace=ADS[temp_ws_name],
    	OutputWorkspace=curr_ws_name,
    	CalFileName='/SNS/VULCAN/shared/CALIBRATION/2017_8_11_CAL/VULCAN_calibrate_2017_08_17.h5', 
    	Params='0.3,-0.001,3.5', 
    	#DMin='0.3', DMax='3.5',
        # edit instrument
        PrimaryFlightPath=43.753999999999998,
        SpectrumIDs='1,2,3',
        L2='2.00944,2.00944,2.00944',
        Polar='90,270,150',
        # about output
        Dspacing=True,
        PreserveEvents=True)
    # PrimaryFlightPath=43, SpectrumIDs='0-2', L2='2,2,2', Polar='90,270,145', Azimuthal='0, 0, 0')
    # print '[DEBUG SNS] EditInstrument to workspace {0}'.format(curr_ws_name)
    # mantid.EditInstrumentGeometry(Workspace=curr_ws_name, PrimaryFlightPath=43.753999999999998, SpectrumIDs='1,2,3', L2='2.00944,2.00944,2.00944', Polar='90,270,150')
    
    print '[DEBUG SNS] Delete workspace {0}'.format(temp_ws_name)
    mantid.DeleteWorkspace(Workspace=temp_ws_name)
else:
    print '[SNS-LIVE] Workspace {0} is not an EventWorkspace or has zero events.'.format(str(ws))
