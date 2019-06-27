"""
DEV/TEST:
	- Test different optimisers and/or loss functions
"""

print("-- SLTM Neural Network: Forex training and testing environment.")

from AIFX_common import *


param_file_path = ""
if len(argv) > 1:
	param_file_path = argv[1]
	if param_file_path[-4:] != ".csv":
		print('- Error in param file - incorrect file type or path.')
else:
	print('- No parameter file specified.')
	exit()

# VARIABLES
training_data_src = r"../data/GBPUSD/GBPUSD_3600.csv"

			
def main(param_file_path):

	sc = MinMaxScaler(feature_range=(0,1))
	
	with open(param_file_path, 'r') as csv_f:
		csv_r  = reader(csv_f)
		params = {param: i for i, param in enumerate(csv_r.__next__())}

		training_data = get_data(training_data_src, price_index=1)
		td_scaled     = sc.fit_transform(training_data)

		for r in csv_r:
			deep_layers = int(r[params['deep_layers']])
			units       = int(r[params['units']])
			dropout     = float(r[params['dropout']])
			epochs      = int(r[params['epochs']])
			batch_size  = int(r[params['batch_size']])
			val_split   = float(r[params['val_split']])
			window      = int(r[params['window']])
			increment   = int(r[params['increment']])
			
			X_train, y_train = shape_training_data(td_scaled, window, increment)
			
			NeuralNet = LSTM_RNN(in_shape   =(X_train.shape[1], 1), \
								 deep_layers=deep_layers,           \
								 units      =units,                 \
								 dropout    =dropout)
								 
			loss_hist = LossHistory()
			time_hist = TimeHistory()
			
			print(deep_layers, units, dropout, epochs, batch_size)
			
			hist = NeuralNet.fit(X_train, y_train, 
						         validation_split=val_split,  \
						         epochs          =epochs,     \
						         batch_size      =batch_size, \
						         callbacks       =[loss_hist, time_hist], shuffle=False)
			
			back_props = int(len(X_train) * (1-val_split) / batch_size) * epochs
			
			result = [deep_layers, units, dropout, epochs, batch_size, back_props, hist.history['loss'][0], hist.history['val_loss'][0], time_hist.train_time]
			log_results('../testing/results/fitness_params_test_results.csv', 'a', results=[result])

	
	
if __name__ == '__main__':
	main(param_file_path)