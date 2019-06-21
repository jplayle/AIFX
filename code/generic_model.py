"""
DEV/TEST:
	- Effect of raw data scaling method and whether to use fit_transform or just transform on the test data set
	- Batch size sensitivity
	- Test different optimisers and/or loss functions
	- Check under/over-fit of model
	- Number of time-steps vs number of epochs
"""

print("-- SLTM Neural Network: Forex training and testing environment.")

import numpy as np
import matplotlib.pyplot as pyplot

from sys import argv, exit
from csv import reader, writer
from time import clock

from keras.models    import Sequential, load_model
from keras.layers    import Dense
from keras.layers    import LSTM
from keras.layers    import Dropout
from keras.callbacks import Callback

from sklearn.preprocessing import MinMaxScaler

# VARIABLES
training_data_src = r"../data/GBPUSD-2016-09_5s.csv"
validate_data_src = r"../data/GBPUSD-2016-10_5s.csv"
predict_data_dst  = r""

window = 60

class LossHistory(Callback):
	def on_train_begin(self, logs={}):
		self.losses = []
		self.val_losses = []

	def on_batch_end(self, batch, logs={}):
		self.losses.append(logs.get('loss'))
		self.val_losses.append(logs.get('val_loss'))

class TimeHistory(Callback):
	def on_train_begin(self, logs={}):
		self.train_time = 0
		self.train_start = clock()

	def on_batch_end(self, batch, logs={}):
		self.train_time += (clock() - self.train_start)
		self.train_start = clock()
		
def get_data(src):
	with open(src, 'r') as csv_f:
		csv_r = reader(csv_f)
		return [r for r in csv_r]

def reshape_fit_data_timesteps(data, window):
	# reshapes data into a series of arrays, each one of length=window and incremented by timestep
	X_train = []
	y_train = []
	for i in range(window, len(data)):
		X_train.append(data[i-window:i, 0])
		y_train.append(data[i, 0])

	X_train, y_train = np.array(X_train), np.array(y_train)
	X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))
	
	return (X_train, y_train)
	
def reshape_fit_data_windows(data, window):
	# reshapes data into series of arrays, each one of length=window and incremented by window
	X_train = []
	y_train = []
	for i in range(int(len(data) / window)):
		X_train.append(data[i*window:(i+1)*window, 0])
		y_train.append([data[(i+1)*window, 0]])
		
	X_train, y_train = np.array(X_train), np.array(y_train)
	X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))
	
	return (X_train, y_train)
	
def LSTM_RNN(in_shape, deep_layers=0, units=80, return_seq=True, dropout=0.2):
	loss_algo = 'mse'
	optimize_algo = 'adam'

	regressor = Sequential()

	regressor.add(LSTM(units = units, return_sequences = True, input_shape = in_shape))
	regressor.add(Dropout(dropout))
	
	for l in range(deep_layers):
		regressor.add(LSTM(units = units, return_sequences = True))
		regressor.add(Dropout(dropout))

	regressor.add(LSTM(units = units))
	regressor.add(Dropout(dropout))

	regressor.add(Dense(units = 1))

	regressor.compile(optimizer = optimize_algo, loss = loss_algo)
	
	return regressor

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

def plot_prediction(path, timestep, window, real_values=[], pred_values=[], title="", y_label="", x_label=""):
	len_rv = len(real_values)
	len_pv = pred_values.size
	pyplot.plot(real_values, [x * timestep for x in range(len_rv)])
	pyplot.plot(pred_values, [window + (x * timestep) for x in range(len_pv)])
	
	pyplot.axis([0, timestep*len_rv, min(min(real_values), min(pred_values)), max(max(real_values), max(pred_values))])
	pyplot.title(title)
	pyplot.ylabel(y_label)
	pyplot.xlabel(x_label)
	pyplot.legend(['Real', 'Predicted'], loc='upper right')
	
	pyplot.savefig(path)

def build_filename(params):
	return "DL%d-U%d-D%d-E%d-BS%d-t%d-w%d" % (params['DL'], params['U'], params['D'], params['E'], params['BS'], params['t'], params['w']) 

	
def main():

	sc1 = MinMaxScaler(feature_range=(0,1))
	sc2 = MinMaxScaler(feature_range=(0,1))

	training_data = get_data(training_data_src)
	validate_data = get_data(validate_data_src)

	training_data_scaled = sc1.transform(training_data)
	validate_data_scaled = sc2.transform(validate_data)

	X_train, y_train = reshape_fit_data_windows(training_data_scaled, window)
	X_eval,  y_eval  = reshape_fit_data_windows(validate_data_scaled, window)

	deep_layers = 0
	units       = 5
	dropout     = 0.2
	epochs      = 5
	batch_size  = 32
	
	NeuralNet = LSTM_RNN(in_shape   =(X_train.shape[1], 1), \
						 deep_layers=deep_layers,           \
						 units      =units,                 \
						 dropout    =dropout)

	loss_hist = LossHistory()
	time_hist = TimeHistory()

	hist = NeuralNet.fit(X_train, y_train,               \
						 validation_data=(X_eval, y_eval), \
						 epochs         =epochs,         \
						 batch_size     =batch_size,     \
						 callbacks      =[loss_hist, time_hist], shuffle=False)
	#NeuralNet.save('m.h5')

	#NeuralNet = load_model("m.h5")
	#eval = NeuralNet.evaluate(X_eval, y_eval, batch_size=batch_size)
	pred = NeuralNet.predict(X_eval, verbose=1)
	pred = sc2.inverse_transform(pred)
	
	result = []
	for x, p_real in enumerate(validate_data):
		try:
			p_pred = pred[x][0]
		except IndexError:
			p_pred = None
		result.append([p_real[0], p_pred])
		
	log_results('../testing/results/pred2.csv', 'a', results=result)
	#plot_prediction(path="../testing/results/graphs/GBPUSD 10-2016.jpg", timestep=5, window=60, real_values=validate_data, pred_values=pred, title="GBPUSD 10-2016", y_label="Price", x_label="Time (s)")
	
	
if __name__ == '__main__':
	main()