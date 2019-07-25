"""
NOTES
- FRANN = Forex Recurrent Artificial Neural Network
- model naming convention: <pair>_<timestep>_<window>_<validTill>.csv
e.g. GBPUSD_3600_60_20200101.h5

"""

from os import listdir
from datetime import date, datetime

from AIFX_common import *



class FRANN_Operations():
	
	def __init__(self):
		self.target_epics = ['CS.D.GBPUSD.CFD.IP']
		
		self.model_dir  = '../models/'
		self.output_dir = '../predictions/' # tbc.

		self.timestep   = 10 #make low in order to debug (see next line after 'while True:' in predictor_loop())
		self.n_tsteps   = 1
		self.sum_tsteps = self.timestep * self.n_tsteps

		self.sub_pred   = 0  #bool - 1, 0 - whether to predict prices between timesteps 
		self.n_sub_pred = 6 * self.sub_pred  #number of points to predict between timesteps (boolean switch applied for later code simplification)
		
		self.layer_pred   = 0 #bool - whether to layered predictions (multiple timesteps shifted to produce a layer of predictions for same point in time) 
		self.n_layer_pred = self.n_tsteps * self.layer_pred #number of other timesteps to use, giving rise to number of prediction layers
		#note: by default, layer predictions are only calculated/shown for timestep 
		
		self.pred_rate = self.timestep #rate at which predictions are updated
		
	def build_window_data(self, data_path ='', timestep=0, window=0):
		"""
		- open relevant epic data file
		- return a list of prices at timestep intervals of length=window
		"""
		return
	
	def predictor_loop(self):

		while True:

			if int(clock()) % self.pred_rate == 0:
				today = date.today()

				for epic in self.target_epics:
					epic_ccy = epic[5:11]

					for model_name in listdir(self.model_dir):
						model_params = model_name.replace('.h5', '').split('_')

						if model_params[0] == epic_ccy:
							FRANN = load_model(self.model_dir + model_name)

							timestep = int(model_params[1])
							window   = int(model_params[2])
							
							valid_till = model_params[3]
							valid_till = date(int(valid_till[:4]), int(valid_till[4:6]), int(valid_till[6:8]))
							if today >= valid_till:
								#don't use models that are deemed out of date
								#send warning that model needs updating
								continue

							sc = MinMaxScaler(feature_range=(0,1))
							
							window_data = self.build_window_data() # COMPLETE THIS FUNCTION!!!
							wd_scaled   = sc.fit_transform(window_data)

							prediction = FRANN.predict(wd_scaled)


		return

		pred = NeuralNet.predict(X_eval, verbose=1)
		pred = sc.inverse_transform(pred)

		result = []

		for x, p_real in enumerate(validate_data):
			try:
				p_pred = pred[x][0]
			except IndexError:
				p_pred = None
			result.append([(x*5)+window, p_real[0], p_pred])

		log_results('../testing/results/pred.csv', 'a', results=result)
		#plot_prediction(path="../testing/results/graphs/GBPUSD 10-2016.jpg", timestep=5, window=60, real_values=validate_data, pred_values=pred, title="GBPUSD 10-2016", y_label="Price", x_label="Time (s)")

		for x in range(pred.size):
			result.append([(x+1)*window*timestep, float(validate_data[(x+1)*window][0]), pred[x][0]])

		#log_results('../testing/results/pred.csv', 'a', results=result)
		plot_prediction(path="../testing/results/graphs/GBPUSD 10-2016.png", timestep=timestep, window=window, results=result, title="GBPUSD 10-2016", y_label="Price", x_label="Time (s)")

	
def main():
	
	run = FRANN_Operations()
	
	run.predictor_loop()
	
if __name__ == '__main__':
	main()