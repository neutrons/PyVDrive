# process the NeXus for simulated diamond powder in VULCAN-X

import os

print (os.getcwd())

# prototype VUCLAN-X with 128 pixels per tube
# nexus_file_name = 'sim_diamon_vulcan_x_prototype.nxs'
# diamond_ws_name = 'sim_c_vulcan-x_prototype'
    
# VULCAN-X phase 1
nexus_file_name = '/home/wzz/Mantid_Project/mantidgeometry/VULCAN-X/simulation/phase1/sim_diamond_vulcan_x.nxs'
diamond_ws_name = 'sim_c_vulcan-x'
ws_index_range = {'B1': (0, 20*8*512),  'B2': (20*8*512, 2* 20*8*512), 'B5': (2* 20*8*512,  2*20*8*512+9*8*256)}

#-----------------------------   REDUCE -------------------------------
if False:
    # reduce
    diamond_ws = Load(Filename=nexus_file_name, OutputWorkspace=diamond_ws_name)
    diamond_ws = ConvertUnits(InputWorkspace=diamond_ws, OutputWorkspace=diamond_ws, Target='dSpacing', EMode='Elastic')
    diamond_ws = Rebin(InputWorkspace=diamond_ws_name, OutputWorkspace=diamond_ws_name, Params='0.3, -0.0003, 3.0')

#-----------------------------   COUNT EVENTS -------------------------------
if False:
    # count events
    diamond_ws = mtd[diamond_ws_name]
    for bank in sorted(ws_index_range.keys()):
        num_events = 0
        for iws in range(ws_index_range[bank][0], ws_index_range[bank][1]):
            num_events += diamond_ws.getSpectrum(iws).getNumberEvents()
        # END-FOR
        print ('{} ({}, {}): {}'.format(bank, ws_index_range[bank][0], ws_index_range[bank][1], num_events))
    # END-FOR
# END-IF

#-----------------------------   FOCUS -------------------------------\
if True:
    # focus
    for bank in sorted(ws_index_range.keys()):
        SumSpectra(InputWorkspace=diamond_ws_name, StartWorkspaceIndex=ws_index_range[bank][0], EndWorkspaceIndex=ws_index_range[bank][1]-1, OutputWorkspace=bank)
    # END-FOR
    
    
    
if False:
    # study the simulated data
    diamond_ws_name = 'sim_c_vulcan-x_prototype'
    diamond_ws = mtd[diamond_ws_name]
    
    num_spec = diamond_ws.getNumberHistograms()
    print ('Number of sepctra = {}'.format(num_spec))
    
    bank_range = {1: (0, 20 * 8 * 128),
                             2: (20 * 8 * 128, 20 * 8 * 128 + 20 * 8 * 128),
                             3: (20 * 8 * 128 * 2, 9 * 8 * 128 + 20 * 8 * 128 * 2)}
                             
    for bank_id in [1, 2, 3]:
        SumSpectra(InputWorkspace=diamond_ws_name, StartWorkspaceIndex=bank_range[bank_id][0], EndWorkspaceIndex=bank_range[bank_id][1]-1,
                            OutputWorkspace='bank{}'.format(bank_id))