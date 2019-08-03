"""
NOTES
- FRANN = Forex Recurrent Artificial Neural Network
- model naming convention: <pair>_<timestep>_<window>_<validTill>.csv
e.g. GBPUSD_3600_60_20200101.h5

"""

from os import listdir
from datetime import date, datetime, timedelta
from time import clock, sleep

import numpy as np
from keras.models import load_model
from sklearn.preprocessing import MinMaxScaler

from AIFX_common_PROD import *


class FRANN_Operations(AIFX_Prod_Variables):
	
	def __init__(self):
		
		AIFX_Prod_Variables.__init__(self)
		
		self.max_data_offset = 0.05
		
		self.load_models()
		
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
			valid_till = model_params[3]
			valid_till = date(int(valid_till[:4]), int(valid_till[4:6]), int(valid_till[6:8]))
			
			self.model_store[epic_ccy][timestep] = {'FRANN':      load_model(self.model_dir + model_file),
													'window':     window,
													'valid_till': valid_till
													}
		
	def build_window_data(self, epic_ccy='', timestep=0, window=0, t_start=None):
		"""
		- open relevant epic data file
		- return a list of prices at timestep intervals of length=window
		- remove ability to return none
		"""
		
		def search_around_blank(data_list, index, r_skip, newf_search=False, _x_prev=0):
			#search for nearby data within +/-x% of timestep e.g. +/- 3 mins
			new_file = False
			
			data_offset = int(r_skip * self.max_data_offset)
			if not newf_search:
				search_rng = (1, data_offset + 1)
			else:
				search_rng = (0, data_offset - _x_prev)
			
			for x in range(search_rng[0], search_rng[1]):
				try:
					data_up = data_list[index + x][self.pred_data_index]
					if data_up != '':
						return data_up
				except IndexError:
					pass
					
				try:
					data_dwn = data_list[index - x][self.pred_data_index]
					if data_dwn != '':
						return data_dwn
				except IndexError:
					return ['newf', x]
					
			return ''
		
		window_data = []
		
		row_skip = int(timestep / self.data_interval_sec)

		data_path  = self.data_dir + epic_ccy + '/'
		data_files = sorted(listdir(data_path))[::-1]
		
		w_len       = 0
		r_skip_newf = 0 #row skip if opening a new file
		srch_newf   = False
		x_prev      = 0
		
		initiate = True
		
		for data_file in data_files:

			with open(data_path + data_file, 'r') as csv_f:
				csv_r = list(reader(csv_f))
				csv_r.pop(0) #remove headers
				
				j = 0
				if initiate:
					for r in csv_r[::-1]:
						data_time = datetime.strptime(r[1], '%Y-%m-%d %H:%M:%S')
						if data_time == t_start:
							r_skip_newf = j
							break
						elif data_time < t_start:
							return []
						j += 1
					initiate = False
										
				if srch_newf:
					srch_newf  = False
					data_point = search_around_blank(csv_r, -1, row_skip, newf_search=True, _x_prev=x_prev)
					try:
						float(data_point)
						window_data.append([data_point])
						w_len += 1
						if w_len == window:
							return window_data[::-1]
					except TypeError:
							return []
			
				for x in range(window - w_len):					
					i = -((x * row_skip) + r_skip_newf) - 1

					try:
						data_point = csv_r[i][self.pred_data_index]
						if data_point == '':
							data_point = search_around_blank(csv_r, i, row_skip)
						try:
							float(data_point)
							window_data.append([data_point])
							w_len += 1
							if w_len == window:
								return window_data[::-1]
						except TypeError:
							if data_point != '':
								srch_newf   = True
								x_prev      = data_point[1]
								r_skip_newf = sum(-1 for r in csv_r) - i - 1 + row_skip
								break
							else:
								return []
								
					except IndexError:
						r_skip_newf = sum(-1 for r in csv_r) - i - 1
						break
						
		if w_len == window:				
			return window_data[::-1]
		else:
			return []
		
	def write_prediction(self, epic_ccy='', timestep=0, dtime=None, price_array=[]):
		"""
		- file name: PAIR_YYYY_M_PRED_TSTEP.csv
		- e.g.:    GBPUSD_2019_7_PRED_3600.csv
		dtime = datetime.datetime object
		"""
	
		fname = self.output_dir + "_".join([epic_ccy, str(dtime.year), str(dtime.month), 'PRED', str(timestep)]) + '.csv'
		
		with open(fname, 'a') as csv_f:
			csv_w = writer(csv_f, lineterminator='\n')
			csv_w.writerow([dtime] + price_array)
	
	def predictor_loop(self):
	
		def utc_now():
			#utc_now = datetime.utcnow().replace(second=0, microsecond=0)
			return datetime.utcnow().replace(second=0, microsecond=0)
		
		t_prev = clock()
		
		while True:
			
			t_now = clock()

			if t_now - t_prev >= self.pred_rate:
				t_start = utc_now() - timedelta(seconds=self.data_interval_sec * 2)
				today   = date.today()
				t_prev  = t_now

				for epic in self.target_epics:
					epic_ccy = epic[5:11]

					if self.pred_layer:
						# code for layered predictions #
						pass
				
					for timestep, model_dict in self.model_store[epic_ccy].items():
						if today > model_dict['valid_till']:
							#don't use models that are deemed out of date
							#send warning that model needs updating
							continue
						
						FRANN  = model_dict['FRANN']
						window = model_dict['window']
						
						sc = MinMaxScaler(feature_range=(0,1))
						
						window_data = self.build_window_data(epic_ccy, timestep, window, t_start)
						if window_data == []:
							continue
						
						window_data = sc.fit_transform(window_data)
						window_data = np.reshape(window_data, (window_data.shape[1], window_data.shape[0], 1))
						
						prediction = FRANN.predict(window_data)
						pred_price = sc.inverse_transform(prediction)[0][0]
						pred_time  = t_start + timedelta(seconds=timestep)
						
						self.write_prediction(epic_ccy, timestep, pred_time, [pred_price])

	
def main():
	
	run = FRANN_Operations()
	
	run.predictor_loop()
	
if __name__ == '__main__':
	main()