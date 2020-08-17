# This script is a prototype for grouping detectors by 2theta value and output a contour plot as d-space vs 2theta
import numpy
from matplotlib import pyplot as plt

"""===========  User Configuration ============="""
IPTS_NUMBER = 19079
RUN_NUMBER = 158581

TWO_THETA_RANGE = [80, 101]  # inclusive on both side
TWO_THETA_STEP = 1.5
RESULT_NAME = 'East-Panel'
# West Bank:  79.21308206662684 to 100.87821654680079, 1771 distinct value
# East Bank:
# High Angle Bank:
"""============================================="""


def create_template_group_ws():
    """ create a template grouping workspace
    :return:
    """
    # Load
    LoadEventNexus(Filename='/SNS/VULCAN/IPTS-22752/nexus/VULCAN_172254.nxs.h5',
                   OutputWorkspace='vulcan_template', MetaDataOnly=True, LoadLogs=False)
    group_ws_name = 'vulcan_group'
    CreateGroupingWorkspace(InputWorkspace='vulcan_template', GroupDetectorsBy='All',
                            OutputWorkspace=group_ws_name)
    return group_ws_name


def main(argv):

    ipts_number = argv[1]
    run_number = argv[2]
    two_theta_bin_range = argv[3]
    two_theta_step = argv[4]
    output_name = argv[5]

    # Load data if necessary
    ws_name = 'VULCAN_{}_events'.format(run_number)
    if not mtd.doesExist(ws_name):
        LoadEventNexus(Filename='/SNS/VULCAN/IPTS-{}/nexus/VULCAN_{}.nxs.h5'.format(ipts_number, run_number),
                       OutputWorkspace=ws_name)

    # Convert unit and binning
    ConvertUnits(InputWorkspace=ws_name, OutputWorkspace=ws_name, Target='dSpacing', AlignBins=True)
    Rebin(InputWorkspace=ws_name, OutputWorkspace=ws_name, Params='0.3,-0.001,3.5', PreserveEvents=False,
          FullBinsOnly=True, IgnoreBinErrors=True)

    event_ws = mtd[ws_name]

    # Determine the output dimension
    two_theta_array = numpy.arange(two_theta_bin_range[0], two_theta_bin_range[1] + two_theta_step,
                                   two_theta_step, dtype='float')
    print('Two theta: {}'.format(two_theta_array))

    grouped_matrix_x = numpy.ndarray(shape=(two_theta_array.shape[0], len(event_ws.readX(0))))
    grouped_matrix_y = numpy.ndarray(shape=(two_theta_array.shape[0], len(event_ws.readY(0))))
    count_vec = numpy.zeros(shape=two_theta_array.shape, dtype='float')

    CreateWorkspace(DataX=grouped_matrix_x, DataY=grouped_matrix_y, NSpec=two_theta_array.shape[0],
                    OutputWorkspace=output_name)
    contour_ws = mtd[output_name]
    for iws in range(two_theta_array.shape[0]):
        contour_ws.dataX(iws)[:] = event_ws.readX(0)[:]

    # source and sample position
    source = event_ws.getInstrument().getSource().getPos()
    sample = event_ws.getInstrument().getSample().getPos()
    # Calculate 2theta for each detectors
    for iws in range(3234, 6468):
        det_i = event_ws.getDetector(iws).getPos()
        two_theta_i = (det_i - sample).angle(sample - source) * 180. / numpy.pi
        i_2theta = numpy.searchsorted(two_theta_array, [two_theta_i])[0]
        if i_2theta < contour_ws.getNumberHistograms():
            contour_ws.dataY(i_2theta)[:] = contour_ws.readY(i_2theta)[:] + event_ws.readY(iws)[:]
            count_vec += 1.
        else:
            print('Spectrum with ws-index {} has 2theta {} (index = {}): out of output contour (2theta) range'
                  ''.format(iws, two_theta_i, i_2theta))
    # END-FOR

    # deal with zero-count-instance
    count_vec[numpy.where(count_vec < 0.1)] = -1

    # normalization
    event_ws = mtd[output_name]
    for iws in range(event_ws.getNumberHistograms()):
        event_ws.dataY(iws)[:] = event_ws.readY(iws)[:]/count_vec[iws]

    return


#
main(['script', IPTS_NUMBER, RUN_NUMBER, TWO_THETA_RANGE, TWO_THETA_STEP, RESULT_NAME])
