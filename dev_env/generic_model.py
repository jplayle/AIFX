"""
NOTES
- observe training data folder structure & file naming
- params: option to get batch params

"""

print("-- SLTM Neural Network: Forex training and testing environment.")

from AIFX_common import *

# VARIABLES
data_root_dir = r'/home/jhp/Dukascopy/'
data_file     = r'GBPUSD_20180717-20190717_3600.csv'
training_data_src = data_root_dir + data_file
data_timestep = extract_training_set_timestep(data_file)

batch_test = False
param_file_path = ''

params = {'timestep':    data_timestep,
		  'window':      60,
		  'increment':   1,
		  'val_split':   0.05,
		  'deep_layers': 0,
		  'units':       80,
		  'dropout':     0.2,
		  'epochs':      50,
		  'batch_size':  32,
		  'loss_algo':   'mae',
		  'optimizer_algo': 'adam'
		 }

	
def main():
	
	timestep = params['timestep']
	window   = params['window']
	
	sc = MinMaxScaler(feature_range=(0,1))

	training_data    = get_data(training_data_src, price_index=1, headers=True)
	td_scaled        = sc.fit_transform(training_data)
	X_train, y_train = shape_training_data(td_scaled, params['window'], params['increment'])
	
	NeuralNet = LSTM_RNN(in_shape   =(X_train.shape[1], 1),
						 deep_layers=params['deep_layers'],
						 units      =params['units'],       
						 dropout    =params['dropout'],
						 loss_algo  =params['loss_algo'],
						 optimizer_algo=params['optimizer_algo']
						 )

	loss_hist = LossHistory()
	time_hist = TimeHistory()

	hist = NeuralNet.fit(X_train, y_train,                     
						 validation_split=params['val_split'], 
						 epochs          =params['epochs'],              
						 batch_size      =params['batch_size'],          
						 callbacks       =[loss_hist, time_hist], shuffle=False)
	#NeuralNet.save('m.h5')

	#NeuralNet = load_model("m1.h5")
	#eval = NeuralNet.evaluate(X_eval, y_eval, batch_size=batch_size)
	
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

	
	
if __name__ == '__main__':
	main()