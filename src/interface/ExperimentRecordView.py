from PyQt4 import QtCore
from PyQt4 import QtGui

import gui.ui_ExperimentRecord as ui_ExperimentRecord


class VulcanExperimentRecordView(QtGui.QMainWindow):
    """
    Reduced live data viewer for VULCAN
    """
    def __init__(self, parent):
        """
        init
        :param parent:
        """
        super(VulcanExperimentRecordView, self).__init__(parent)

        self.ui = ui_ExperimentRecord.Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.tableWidget_recordsInfoTable.setup()

        return


    def launch_live_data_processor(self):
        """

        :return:
        """
        #  post processing test
        CreateWorkspace(OutputWorkspace='counter', DataX=[0], DataY=[0], NSpec=1)
        post_script_name = '/home/wzz/Mantid_Project/builds/vulcan_live_data_test.py'

        # Test for script: whatever has all the log information...
        # and output_1, output_2 will do good still
        StartLiveData(UpdateEvery=5, Instrument='VULCAN', Listener='SNSLiveEventDataListener',
                      Address='bl7-daq1.sns.gov:31415', StartTime='1990-01-01T00:00:00',
                      ProcessingScriptFilename=post_script_name,
                      PreserveEvents=False,
                      # AccumulationWorkspace='live_vulcan_x',
                      AccumulationMethod='Add',
                      OutputWorkspace='whatever')


    def live_monitor(self):
        """

        :return:
        """
        from datetime import datetime

        # Now get the data, read the first spectra
        spectra = input.readY(0)
        # extract the first value from the array
        count = spectra[0]

        count = input.getNumberEvents()

        # output it as a log message
        logger.notice("Total counts so far " + str(count))

        # if my ouput workspace has not been created yet, create it.
        if not mtd.doesExist(output):
            table = CreateEmptyTableWorkspace(OutputWorkspace=output)
            table.setTitle("Event Rate History")
            table.addColumn("str", "Time")
            table.addColumn('str', 'EventsS')
            table.addColumn("int", "Events")

        table = mtd[output]


    def live_reduce(self):
        ws = input
        counter_ws = mtd['counter']

        index = int(counter_ws.readX(0)[0])

        print 'index = ', index
        counter_ws.dataX(0)[0] += 1

        print 'Iteration {0}: Number of events = {0}'.format(index, ws.getNumberEvents())

        curr_ws_name = 'output_{0}'.format(index)
        CloneWorkspace(InputWorkspace=input, OutputWorkspace=curr_ws_name)
        Rebin(InputWorkspace=input, OutputWorkspace=output, Params='5000., -0.001, 50000.')
        AlignAndFocusPowder(InputWorkspace=mtd[curr_ws_name],
                            OutputWorkspace=curr_ws_name,
                            CalFileName='/SNS/VULCAN/shared/CALIBRATION/2017_8_11_CAL/VULCAN_calibrate_2017_08_17.h5',
                            Params='-0.001',
                            DMin='0.5', DMax='3.5', PreserveEvents=False)
        # PrimaryFlightPath=43, SpectrumIDs='0-2', L2='2,2,2', Polar='90,270,145', Azimuthal='0, 0, 0')
        EditInstrumentGeometry(Workspace=curr_ws_name, PrimaryFlightPath=50, L2='2,2,2', Polar='90,270,150')




