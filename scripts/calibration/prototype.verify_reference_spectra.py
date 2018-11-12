"""
panel 0: ws-index = 535, detid = 26785
panel 1: ws-index = 1613, detid = 28035
panel 2: ws-index = 2691, detid = 29285
panel 3: ws-index = 3769, detid = 33035
panel 4: ws-index = 4847, detid = 34285
panel 5: ws-index = 5925, detid = 35535
"""

ws = mtd['full_diamond']

# west bank
for ws_index in [535, 1613, 2691]:
    detector = ws.getDetector(ws_index)
    print ('WorkspaceIndex = {0}.  Detector ID = {1}.  Detector @ {2}'.format(ws_index, detector.getID(), detector.getPos()))
    
    
# east bank
for ws_index in [3769, 4847, 5925]:
    detector = ws.getDetector(ws_index)
    print ('WorkspaceIndex = {0}.  Detector ID = {1}.  Detector @ {2}'.format(ws_index, detector.getID(), detector.getPos()))
    
    
# high angle bank
# panel 6: ws-index = 15555, detid = 71587
for ws_index in [15555]:
    detector = ws.getDetector(ws_index)
    print ('WorkspaceIndex = {0}.  Detector ID = {1}.  Detector @ {2}'.format(ws_index, detector.getID(), detector.getPos()))