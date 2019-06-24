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

params = {'timestep':    5,
		  'window':      1000,
		  'deep_layers': 0,
		  'units':       100,
		  'dropout':     0.2,
		  'epochs':      5,
		  'batch_size':  32
		 }

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
	print('Logging results...')
	with open(path, mode) as csv_f:
		csv_w = writer(csv_f, lineterminator='\n')
		for r in results:
			csv_w.writerow([i for i in r])

def plot_prediction(path, timestep, window, results, title="", y_label="", x_label=""):
	# results format = [time(s), p_real, p_pred]
	
	print('Plotting results...')
	t_array = [x[0] for x in results]
	pyplot.plot(t_array, [x[1] for x in results])
	pyplot.plot(t_array, [x[2] for x in results])
	
	#pyplot.axis([0, timestep*len_rv, min(min(real_values), min(pred_values)), max(max(real_values), max(pred_values))])
	pyplot.title(title)
	pyplot.ylabel(y_label)
	pyplot.xlabel(x_label)
	pyplot.legend(['Real', 'Predicted'], loc='upper right')
	
	pyplot.savefig(path)

def build_filename(params):
	return "DL%d-U%d-D%d-E%d-BS%d-t%d-w%d" % (params['DL'], params['U'], params['D'], params['E'], params['BS'], params['t'], params['w']) 

	
def main():
	
	timestep = params['timestep']
	window =   params['window']
	
	sc = MinMaxScaler(feature_range=(0,1))

	training_data = get_data(training_data_src)
	validate_data = get_data(validate_data_src)
	validate_data = validate_data[:int(len(validate_data)/5)]
 
	sc.fit_transform(training_data + validate_data)

	training_data_scaled = sc.transform(training_data)
	validate_data_scaled = sc.transform(validate_data)
	
	X_train, y_train = reshape_fit_data_windows(training_data_scaled, window)
	X_eval,  y_eval  = reshape_fit_data_windows(validate_data_scaled, window)

	
	NeuralNet = LSTM_RNN(in_shape   =(X_train.shape[1], 1), \
						 deep_layers=params['deep_layers'], \
						 units      =params['units'],       \
						 dropout    =params['dropout'])

	loss_hist = LossHistory()
	time_hist = TimeHistory()

	NeuralNet.fit(X_train, y_train,                  \
			   validation_data=(X_eval, y_eval),     \
			   epochs         =params['epochs'],     \
			   batch_size     =params['batch_size'], \
			   callbacks      =[loss_hist, time_hist], shuffle=False)
	#NeuralNet.save('m1.h5')

	#NeuralNet = load_model("m1.h5")
	#eval = NeuralNet.evaluate(X_eval, y_eval, batch_size=batch_size)
	pred = NeuralNet.predict(X_eval, verbose=1)
	pred = sc.inverse_transform(pred)
	
	result = []
	for x in range(pred.size):
		result.append([(x+1)*window*timestep, float(validate_data[(x+1)*window][0]), pred[x][0]])
		
	#log_results('../testing/results/pred.csv', 'a', results=result)
	plot_prediction(path="../testing/results/graphs/GBPUSD 10-2016.png", timestep=timestep, window=window, results=result, title="GBPUSD 10-2016", y_label="Price", x_label="Time (s)")
	
	
if __name__ == '__main__':
	main()