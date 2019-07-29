import numpy as np
import matplotlib.pyplot as pyplot

from sys import argv, exit
from csv import reader, writer
from time import clock, sleep

from keras.models import load_model

from sklearn.preprocessing import MinMaxScaler



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
		self.target_epics = self.crypto_epics + self.fiat_epics
		
		self.data_interval_str   = "1MIN"
		self.data_interval_int   = 1
		self.data_interval_units = 60
		self.data_interval_sec   = self.data_interval_int * self.data_interval_units
		
		self.data_dir   = 'historic_data/'
		self.model_dir  = 'models/'
		self.output_dir = 'predicted_data/' #tbc
		
		self.pred_layer = 0  # boolean switch for layer predictions 
		self.layer_cap  = 0  # 0 = none a.k.a. no limit - use all layers 
		
		self.pred_rate  = 10 #self.data_interval_int * 60 
		
		self.pred_data_index = 2 #column for data extraction

		
		
def get_data(src, subset=(0,-1), price_index=1, headers=False):
	# src: relative path to .csv file containing data.
	# Return type: list, data is strings as found in csv.
	with open(src, 'r') as csv_f:
		csv_r = reader(csv_f)
		if headers:
			csv_r.__next__()
		return [[r[price_index]] for r in csv_r[subset[0]:subset[1]]]

	
def predict(data, RNN):
	X_test = np.array(data)
	X_test = np.reshape(X_predict, (X_predict.shape[0], X_predict.shape[1], 1))
	
	return RNN.predict(data)
	
	
def forecast(data, RNN, fwd_steps=1):
	X_predict = np.array([data])
	X_predict = np.reshape(X_predict, (X_predict.shape[0], X_predict.shape[1], 1))

	price_predictions = []
	for i in range(fwd_steps):
		predicted_price = RNN.predict(X_predict)[0]
		
		price_predictions.append(predicted_price)
		
		data = np.delete(data, 0)
		data = np.append(data, predicted_price)
		
		X_predict = np.array([data])
		X_predict = np.reshape(X_predict, (X_predict.shape[0], X_predict.shape[1], 1))
		
	return price_predictions

def log_results(path='', mode='a', results=[]):
	#results: array of lists where each list is a row to be written. 
	with open(path, mode) as csv_f:
		csv_w = writer(csv_f, lineterminator='\n')
		for r in results:
			csv_w.writerow([i for i in r])

			
def plot_prediction(_path, timestep, window, real_values=[], pred_values=[], title="", y_label="", x_label=""):
	len_rv = len(real_values)
	len_pv = pred_values.size
	pyplot.plot(real_values, [x * timestep for x in range(len_rv)])
	pyplot.plot(pred_values, [window + (x * timestep) for x in range(len_pv)])
	
	pyplot.axis([0, timestep*len_rv, min(min(real_values), min(pred_values)), max(max(real_values), max(pred_values))])
	pyplot.title(title)
	pyplot.ylabel(y_label)
	pyplot.xlabel(x_label)
	pyplot.legend(['Real', 'Predicted'], loc='upper right')
	
	pyplot.savefig(_path)