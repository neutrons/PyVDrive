# process the NeXus for simulated diamond powder in VULCAN-X

if False:
    # prototype VUCLAN-X with 128 pixels per tube
    nexus_file_name = 'sim_diamon_vulcan_x_prototype.nxs'
    diamond_ws_name = 'sim_c_vulcan-x_prototype'
    diamond_ws = Load(Filename=nexus_file_name, OutputWorkspace=diamond_ws_name)
    
    diamond_ws = ConvertUnits(InputWorkspace=diamond_ws, OutputWorkspace=diamond_ws, Target='dSpacing', EMode='Elastic')
    diamond_ws = Rebin(InputWorkspace=diamond_ws_name, OutputWorkspace=diamond_ws_name, Params='0.3, -0.0003, 3.0')
    
if True:
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