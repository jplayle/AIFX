"""
NOTES
- FRANN = Forex Recurrent Artificial Neural Network
- model naming convention: <pair>_<timestep>_<window>_<validTill>.csv
e.g. GBPUSD_3600_60_20200101.h5

"""

from os import listdir
from datetime import date, datetime, timedelta

from AIFX_common_PROD import *



class FRANN_Operations(AIFX_Prod_Variables):
	
	def __init__(self):
		
		AIFX_Prod_Variables.__init__(self)
		
		self.timestep   = 10 #make low in order to debug (see next line after 'while True:' in predictor_loop())
		self.n_tsteps   = 1
		self.sum_tsteps = self.timestep * self.n_tsteps

		self.sub_pred   = 0  #bool - 1, 0 - whether to predict prices between timesteps 
		self.n_sub_pred = 6 * self.sub_pred  #number of points to predict between timesteps (boolean switch applied for later code simplification)
		
		self.layer_pred   = 0 #bool - whether to layered predictions (multiple timesteps shifted to produce a layer of predictions for same point in time) 
		self.n_layer_pred = self.n_tsteps * self.layer_pred #number of other timesteps to use, giving rise to number of prediction layers
		#note: by default, layer predictions are only calculated/shown for timestep 
		
		self.pred_rate = self.timestep #rate at which predictions are updated
		
		self.load_models()
		
	def load_models(self):
		"""
		- check how big FRANN will be - can they all be held in RAM?
		If not, must load models individually if a large number are to be used.
		Make sure to be using the bare bones NN - toggle off the optimizer state.
		"""
		self.model_store = {epic[5:11]: {} for epic in self.target_epics}
		
		for FRANN in listdir(self.model_dir):
			model_params = model_name.replace('.h5', '').split('_')
			
			epic_ccy   = model_params[0]
			timestep   = int(model_params[1])
			window     = int(model_params[2])
			valid_till = model_params[3]
			valid_till = date(int(valid_till[:4]), int(valid_till[4:6]), int(valid_till[6:8]))
			
			self.model_store[epic_ccy][timestep] = {'FRANN':      load_model(FRANN),
													'window':     window,
													'valid_till': valid_till
													} 
			
		return
		
	def build_window_data(self, data_path ='', timestep=0, window=0):
		"""
		- open relevant epic data file
		- return a list of prices at timestep intervals of length=window
		"""
		return
		
	def write_prediction(self, epic_ccy='', timestep=0, dtime=None, price=0):
		"""
		- file name: PAIR_YYYY_M_PRED_TSTEP.csv
		- e.g.:    GBPUSD_2019_7_PRED_3600.csv
		dtime = datetime.datetime object
		"""
		fpath = '' #tbc
		fname = fpath + "_".join([epic_ccy, dtime.year, dtime.month, 'PRED', timestep, '.csv'])
		
		with open(fname, 'a') as csv_w:
			csv_w = writer(csv_f, lineterminator='\n')
			csv_w.writerow([dtime, price])
			
		return 
	
	def predictor_loop(self):

		while True:

			if int(clock()) % self.pred_rate == 0:
				today = date.today()
				tnow  = datetime.utcnow()

				for epic in self.target_epics:
					epic_ccy = epic[5:11]
				
					for timestep, model_dict in self.model_store[epic[epic_ccy]].items():
						if today > model_dict['valid_till']:
							#don't use models that are deemed out of date
							#send warning that model needs updating
							continue
							
						FRANN  = model_dict['FRANN']
						window = model_dict['window']

						sc = MinMaxScaler(feature_range=(0,1))
						
						#window_data = self.build_window_data() # COMPLETE THIS FUNCTION!!!
						#wd_scaled   = sc.fit_transform(window_data)

						#prediction = FRANN.predict(wd_scaled)
						#pred_price = sc.inverse_transform(prediction)
						pred_time  = tnow + timedelta(timestep)
						print(pred_time)
						#self.write_prediction(epic_ccy, timestep, pred_time, pred_price)

	
def main():
	
	run = FRANN_Operations()
	
	run.predictor_loop()
	
if __name__ == '__main__':
	main()