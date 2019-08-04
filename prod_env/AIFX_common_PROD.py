"""
AIFX Production Environment - Common Variables & Functions. 
"""
from csv import reader, writer
from datetime import datetime

class AIFX_Prod_Variables():
	
	def __init__(self):
		self.crypto_epics = ["CS.D.BITCOIN.CFD.IP", "CS.D.ETHUSD.CFD.IP", "CS.D.LTCUSD.CFD.IP", "CS.D.XRPUSD.CFD.IP"]
		self.fiat_epics   = ["CS.D.GBPUSD.CFD.IP", 
							 "CS.D.USDJPY.CFD.IP", 
							 "CS.D.EURGBP.CFD.IP", 
							 "CS.D.EURJPY.CFD.IP", 
							 "CS.D.EURUSD.CFD.IP", 
							 "CS.D.GBPJPY.CFD.IP",	
							 "CS.D.AUDJPY.CFD.IP", 
							 "CS.D.AUDUSD.CFD.IP", 
							 "CS.D.AUDCAD.CFD.IP", 
							 "CS.D.USDCAD.CFD.IP", 
							 "CS.D.NZDUSD.CFD.IP", 
							 "CS.D.NZDJPY.CFD.IP",	
							 "CS.D.AUDEUR.CFD.IP", 
							 "CS.D.AUDGBP.CFD.IP", 
							 "CS.D.CADJPY.CFD.IP", 
							 "CS.D.NZDGBP.CFD.IP", 
							 "CS.D.NZDEUR.CFD.IP", 
							 "CS.D.NZDCAD.CFD.IP"]
		self.target_epics = self.fiat_epics + self.crypto_epics
		
		self.data_interval_str   = "1MINUTE"
		self.data_interval_int   = 1
		self.data_interval_units = 60
		self.data_interval_sec   = self.data_interval_int * self.data_interval_units
		
		self.data_dir   = 'historic_data/'
		self.model_dir  = 'models/'
		self.output_dir = 'predicted_data/' #tbc
		
		self.pred_layer = 0  # boolean switch for layer predictions 
		self.layer_cap  = 0  # 0 = none a.k.a. no limit - use all layers 
		
		self.pred_rate  = self.data_interval_sec
		
		self.pred_data_index = 2 #column for data extraction
	
class FileNaming():

	def historic_data_filename(self, dir_path, epic_ccy, t_curr):
		suffix = '.csv'
		fname  = '-'.join([epic_ccy, str(t_curr.year), str(t_curr.month)]) + suffix
		return dir_path + '/'.join([epic_ccy, fname])
	
	def predicted_data_filename(self, dir_path, epic_ccy, dtime, timestep):
		suffix = '.csv'
		fname  = '_'.join([epic_ccy, str(dtime.year), str(dtime.month), 'PRED', str(timestep)]) + '.csv'
		return dir_path + '/'.join([epic_ccy, fname])

def get_data(src, subset=(0,-1), price_index=1, headers=False):
	# src: relative path to .csv file containing data.
	# Return type: list, data is strings as found in csv.
	with open(src, 'r') as csv_f:
		csv_r = reader(csv_f)
		if headers:
			csv_r.__next__()
		return [[float(r[price_index])] for r in csv_r[subset[0]:subset[1]]]