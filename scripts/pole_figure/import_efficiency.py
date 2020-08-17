import h5py
import math

vulcan_eff_file = h5py.File(
    '/SNS/users/wzz/Projects/VULCAN/PoleFigure/vulcan_eff_156473.hdf5', 'r')
print vulcan_eff_file.keys()
print vulcan_eff_file['entry']['detector_efficiency'].keys()
efficiency = vulcan_eff_file['entry']['detector_efficiency']['inversed efficiency']

print type(efficiency)
print dir(efficiency)
efficiency = efficiency[:]
vulcan_eff_file.close()

eff_ws = CreateWorkspace(DataX=range(1, efficiency.size+1),
                         DataY=efficiency, NSpec=efficiency.size)

for iws in range(eff_ws.getNumberHistograms()):
    inv_eff_i = eff_ws.readY(iws)[0]
    if math.isnan(inv_eff_i):
        print iws
    elif math.isinf(inv_eff_i) or inv_eff_i > 100:
        eff_ws.dataY(iws)[0] = 1.
