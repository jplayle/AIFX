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
#import matplotlib.pyplot as pyplot

from sys import argv, exit
from csv import reader, writer

from keras.models    import Sequential, load_model
from keras.layers    import Dense
from keras.layers    import LSTM
from keras.layers    import Dropout
from keras.callbacks import Callback

from sklearn.preprocessing import MinMaxScaler

#change
if len(argv) > 1:
	param_file_path = argv[1]
	if param_file_path[-4:] != ".csv":
		print('Error in param file - incorrect file type or path.')
else:
	exit()

# VARIABLES
training_data_src = "GBPUSD-2016-09_5s.csv"
validate_data_src = "GBPUSD-2016-10_5s.csv"
predict_data_dst  = ""

timesteps = 60
n_epochs  = 1
bat_size  = 32

class LossHistory(Callback):
	def on_train_begin(self, logs={}):
		self.losses = []
		self.val_losses = []

	def on_batch_end(self, batch, logs={}):
		self.losses.append(logs.get('loss'))
		self.val_losses.append(logs.get('val_loss'))

def get_data(src):
	with open(src, 'r') as csv_f:
		csv_r = reader(csv_f)
		return [r for r in csv_r]

def reshape_fit_data(data, timesteps):
	X_train = []
	y_train = []
	for i in range(timesteps, len(data)):
		X_train.append(data[i-timesteps:i, 0])
		y_train.append(data[i, 0])

	X_train, y_train = np.array(X_train), np.array(y_train)
	X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))
	
	return (X_train, y_train)
	
def LSTM_RNN(n_deep_layers=0, units=50, return_seq=True, dropout=0.2):
	loss_algo = 'mse'
	optimize_algo = 'adam'

	regressor = Sequential()

	regressor.add(LSTM(units = units, return_sequences = True, input_shape = (X_train.shape[1], 1)))
	regressor.add(Dropout(dropout))

	regressor.add(LSTM(units = units, return_sequences = True))
	regressor.add(Dropout(dropout))

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

def log_results(path='results.csv', mode='a', results=[]):
	with open(path, mode) as csv_f:
		csv_w = writer(csv_f, lineterminator='\n')
		for r in results:
			csv_w.writerow([r])

def main(param_file_path):
	
	with open(param_file_path, 'r') as csv_f:
		csv_r  = reader(csv_f)
		params = {param: i for i, param in enumerate(csv_r.next())}
			
	sc = MinMaxScaler(feature_range=(0,1))

	training_data        = get_data(training_data_src)
	validate_data        = get_data(validate_data_src)

	training_data_scaled = sc.fit_transform(training_data)
	validate_data_scaled = sc.fit_transform(validate_data)

	X_train, y_train     = reshape_fit_data(training_data_scaled, timesteps)
	X_val,   y_val       = reshape_fit_data(validate_data_scaled, timesteps)


	NeuralNet = LSTM_RNN(n_deep_layers=params['deep_layers'],
						 units        =params['layers'],
						 dropout      =params['dropout'])
	history   = LossHistory()
	NeuralNet.fit(X_train, y_train, 
				  validation_data=(X_val, y_val),
				  epochs=params['epochs'],
				  batch_size=params['batch_size'],
				  callbacks=[history])

	
	
if '__name__' = __main__():
	main()
	
	
	
"""
#NeuralNet.save('m.h5')
#NeuralNet = load_model('m.h5')

#price_predictions = forecast(test_data_scaled, NeuralNet, fwd_steps=10)
#price_predictions = sc.inverse_transform(price_predictions)

#log_results('results.csv', 'w')
train_loss = history.losses
val_loss   = history.val_losses
print(len(train_loss), len(val_loss))
print(type(train_loss), type(val_loss))

max_i = min(len(train_loss), len(val_loss))
pyplot.plot(train_loss[:max_i])
pyplot.plot(val_loss[:max_i])
pyplot.title('model train vs validation loss')
pyplot.ylabel('loss')
pyplot.xlabel('epoch')
pyplot.legend(['train', 'validation'], loc='upper right')
pyplot.show()
"""