"""
AIFX Production Environment - Common Variables & Functions. 
"""
from os import listdir
from csv import reader, writer
from datetime import date, datetime
from datetime import time as dt_time

from keras.models import load_model

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
		
		self.data_written_buffer = 2 #shift prediction time back n rows so it's guaranteed all data for that timestamp will have been written
		
		self.FX_market_global_open_t  = dt_time(hour=20) #open hour MUST be in GMT/UTC as a stationary reference (doesn't change for DST etc) 
		self.FX_market_global_close_t = dt_time(hour=21) #close hour MUST be in GMT/UTC as a stationary reference (doesn't change for DST etc)
		
	def load_models(self):
		"""
		- check how big FRANN will be - can they all be held in RAM?
		If not, must load models individually if a large number are to be used.
		Make sure to be using the bare bones NN - toggle off the optimizer state.
		"""
		self.model_store = {epic[5:11]: {} for epic in self.target_epics}

		for model_file in listdir(self.model_dir):
			model_params = model_file.replace('.h5', '').split('_')
			
			epic_ccy   = model_params[0]
			timestep   = int(model_params[1])
			window     = int(model_params[2])
			stdev_diff = float(model_params[4].replace('#', '.'))

			valid_till = model_params[3]
			valid_till = date(int(valid_till[:4]), int(valid_till[4:6]), int(valid_till[6:8]))

			self.model_store[epic_ccy][timestep] = {'FRANN':  load_model(self.model_dir + model_file),
												'window':     window,
												'valid_till': valid_till,
												'err_stdev':  stdev_diff
												}
	
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