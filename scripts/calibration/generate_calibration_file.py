# Generate VULCAN's calibration
from  cross_correlation_lib import *

def main(argv):
    """

    :param argv:
    :return:
    """
    if len(argv) == 0:
        # default
        working_dir = '/SNS/users/wzz/Projects/VULCAN/nED_Calibration/Diamond_NeXus/'
        nxs_file_name = os.path.join(working_dir, 'VULCAN_150178_HighResolution_Diamond.nxs')
    else:
        # user specified
        nxs_file_name = argv[0]

    # decide to load or not and thus group workspace
    diamond_ws_name, group_ws_name = initialize_calibration(nxs_file_name, False)
        
    # cross_correlate_vulcan_data(diamond_ws_name, group_ws_name)
    
    cross_correlate_vulcan_data(diamond_ws_name, group_ws_name, fit_time=2, flag='2fit')


def analysize_mask():
    """
    """


def analyze_result():
    # WEST
    calculate_model('cc_vulcan_diamond_west', 1755, 'offset_vulcan_diamond_west_FitResult')
    # plot cost list
    cost_list, west_bad = evaluate_cc_quality('cc_vulcan_diamond_west', 'offset_vulcan_diamond_west_FitResult')
    cost_array = numpy.array(cost_list).transpose()
    CreateWorkspace(DataX=cost_array[0], DataY=cost_array[1], NSpec=1, OutputWorkspace='West_Cost')
    
    
    # East
    # plot cost list
    cost_list, east_bad = evaluate_cc_quality('cc_vulcan_diamond_east', 'offset_vulcan_diamond_east_FitResult')
    cost_array = numpy.array(cost_list).transpose()
    print (cost_array)
    CreateWorkspace(DataX=cost_array[0], DataY=cost_array[1], NSpec=1, OutputWorkspace='East_Cost')
    
    # HIGH ANGLE
    calculate_model('cc_vulcan_diamond_high_angle', 12200, 'offset_vulcan_diamond_high_angle_FitResult')
    # plot cost list
    cost_list, high_angle_bad = evaluate_cc_quality('cc_vulcan_diamond_high_angle', 'offset_vulcan_diamond_high_angle_FitResult')
    cost_array = numpy.array(cost_list).transpose()
    CreateWorkspace(DataX=cost_array[0], DataY=cost_array[1], NSpec=1, OutputWorkspace='HighAngle_Cost')

main([])





