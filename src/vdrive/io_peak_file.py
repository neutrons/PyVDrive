########
# Read/Write peak file in GSAS format for single peak fitting
#
# $ bank, name, number of peak, position, width					
# 1	bcc110	2	2.101	2.07	0.03
# 1	Fcc111	2	2.173	2.028	0.03
# 1	Fcc200	1	1.879	0.035	
# 1	bcc200	1	1.486	0.03	
# 1	Fcc220	1	1.326	0.03	
# 1	bcc211	1	1.214	0.03	
# 1	Fcc311	1	1.134	0.03	
# 1	Fcc222	2	0.9374	1.017	0.03
# $1 	Bcc220	2	1.017	1.039	0.03
# $1 	bcc310FCC400	1	0.9039	0.03	
# $1 	bcc222	2	0.829	0.8038	0.02
# $1 	fcc331	2	0.8038	0.83	0.02
# $1 	bcc321	1	0.768	0.02	
# $ bank, name, number of peak, position, width					
# 2	bcc110	2	2.101	2.07	0.03
# 2	Fcc111	2	2.173	2.028	0.03
# 2	Fcc200	1	1.879	0.035	
# 2	bcc200	1	1.486	0.03	
# 2	Fcc220	1	1.326	0.03	
# 2	bcc211	1	1.214	0.03	
# 2	Fcc311	1	1.134	0.03	
# 2	Fcc222	2	0.9374	1.017	0.03
# $2 	Bcc220	2	1.017	1.039	0.03
# $2 	bcc310FCC400	1	0.9039	0.03	
# $2 	bcc222	2	0.829	0.8038	0.02
# $2 	fcc331	2	0.8038	0.83	0.02
# $2 	bcc321	1	0.768	0.02	
########


class GSASPeakFileManager(object):
    def __init__(self):
        """

        :return:
        """
        pass

    def add_peak(self, bank, name, position, width):
        """
        TODO/NOW: doc and implement
        :param bank:
        :param name:
        :param position:
        :param width:
        :return:
        """
        pass

    def delete_peak(self, bank, name):
        """
        TODO/NOW: doc and implement
        :param bank:
        :param name:
        :return:
        """
        pass

    def export_peaks(self, peak_file):
        """
        TODO/NOW: doc and implement
        :param peak_file:
        :return:
        """
        pass

    def import_peaks(self, peak_file):
        """
        TODO/NOW: doc and implement
        :param peak_file:
        :return:
        """
        pass


    def get_number_peaks(self):
        """
        TODO/NOW: doc and implement
        :param peak_file:
        :return:
        """
        pass