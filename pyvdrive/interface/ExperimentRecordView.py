from PyQt4 import QtCore
from PyQt4 import QtGui

import gui.ui_ExperimentRecord_ui as ui_ExperimentRecord


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

        print 'Iteration {0}: Number of events = {1}'.format(index, ws.getNumberEvents())

        curr_ws_name = 'output_{0}'.format(index)
        CloneWorkspace(InputWorkspace=input, OutputWorkspace=curr_ws_name)
        Rebin(InputWorkspace=input, OutputWorkspace=output, Params='5000., -0.001, 50000.')
        AlignAndFocusPowder(InputWorkspace=mtd[curr_ws_name],
                            OutputWorkspace=curr_ws_name,
                            CalFileName='/SNS/VULCAN/shared/CALIBRATION/2017_8_11_CAL/VULCAN_calibrate_2017_08_17.h5',
                            Params='-0.001',
                            DMin='0.5', DMax='3.5', PreserveEvents=False)
        # PrimaryFlightPath=43, SpectrumIDs='0-2', L2='2,2,2', Polar='90,270,145', Azimuthal='0, 0, 0')
        print '[SpecialDebug] Interface... EditInstrument on {0}'.format(curr_ws_name)
        EditInstrumentGeometry(Workspace=curr_ws_name, PrimaryFlightPath=43.753999999999998,
                               SpectrumIDs='1,2,3',
                               L2='2.00944,2.00944,2.00944', Polar='90,270,150')

