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


def extract_training_set_timestep(data_file=''):
	return int(data_file.split("_")[-1].replace('.csv', ''))

class LossHistory(Callback):
	# Keras callback object for logging loss history during training.
	# There is only 1 validation loss per epoch.
	def on_train_begin(self, logs={}):
		self.losses = []
		self.val_losses = []

	def on_batch_end(self, batch, logs={}):
		self.losses.append(logs.get('loss'))
		self.val_losses.append(logs.get('val_loss'))

class TimeHistory(Callback):
	# Keras callback object for tracking the time taken to traing the model.
	def on_train_begin(self, logs={}):
		self.train_time = 0
		self.train_start = clock()

	def on_batch_end(self, batch, logs={}):
		self.train_time += (clock() - self.train_start)
		self.train_start = clock()
		
		
def get_data(src, subset=(0,-1), price_index=1, headers=False):
	# src: relative path to .csv file containing data.
	# Return type: list, data is strings as found in csv.
	with open(src, 'r') as csv_f:
		csv_r = reader(csv_f)
		if headers:
			csv_r.__next__()
		return [[r[price_index]] for r in csv_r[subset[0]:subset[1]]]
	
def shape_training_data(data, window=5, increment=1):
	# data:      numpy ndarray of normalised/scaled data points for training on.
	# window:    integer - number of previous data points to use per prediction. 
	# increment: integer - how many timesteps to shift the window each time.
	_X = []
	_y = []
	for x in range(int((len(data) - window) / increment)):
		i = x * increment
		j = i + window
		_X.append(data[i:j, 0])
		_y.append(data[j, 0])
		
	_X, y = np.array(_X), np.array(_y)
	_X    = np.reshape(_X, (_X.shape[0], _X.shape[1], 1))
	
	return (_X, _y)
	
	
def LSTM_RNN(in_shape, deep_layers=0, units=80, return_seq=True, dropout=0.2, loss_algo='mse', optimizer_algo='adam'):

	regressor = Sequential()

	regressor.add(LSTM(units=units, return_sequences=True, input_shape=in_shape))
	regressor.add(Dropout(dropout))
	
	for l in range(deep_layers):
		regressor.add(LSTM(units=units, return_sequences=True))
		regressor.add(Dropout(dropout))

	regressor.add(LSTM(units=units))
	regressor.add(Dropout(dropout))

	regressor.add(Dense(units=1))

	regressor.compile(optimizer=optimizer_algo, loss=loss_algo)
	
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

	
def build_filename(params):
	return "DL%d-U%d-D%d-E%d-BS%d-t%d-w%d" % (params['DL'], params['U'], params['D'], params['E'], params['BS'], params['t'], params['w']) 