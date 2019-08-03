"""
NOTES
- observe training data folder structure & file naming
- params: option to get batch params

"""

print("-- SLTM Neural Network: Forex training and testing environment.")

from AIFX_common_DEV import *

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
		  'epochs':      40,
		  'batch_size':  32,
		  'loss_algo':   'mse',
		  'optimizer_algo': 'adam'
		 }

	
def main(train=True, save=True, predict=False, model_name=''):
	
	timestep = params['timestep']
	window   = params['window']
	
	sc = MinMaxScaler(feature_range=(0,1))
	
	if train:
		training_data    = get_data(training_data_src, price_index=1, headers=True)
		td_scaled        = sc.fit_transform(training_data)
		X_train, y_train = shape_data(td_scaled, params['window'], params['increment'])

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
		if save:
			fname = '_'.join(['GBPUSD', str(params['timestep']), str(params['window']), '20200101', '.h5'])
			NeuralNet.save(fname)

	if predict and model_name:
		NeuralNet = load_model(model_name)
		
		predict_data   = get_data(training_data_src, price_index=1, headers=True)
		pd_scaled      = sc.fit_transform(predict_data)
		X_pred, y_pred = shape_data(pd_scaled, 60, 1)
		
		predictions = []
		
		d_len = sum(1 for x in X_pred)
		for n in range(d_len):
			_X = X_pred[n]
			_X = np.reshape(_X, (_X.shape[1], _X.shape[0], 1))
			
			pred = sc.inverse_transform(NeuralNet.predict(_X))[0][0]
			real = sc.inverse_transform([[y_pred[n]]])[0][0]
			
			predictions.append([real, pred, (abs(real - pred) / real)*100])
		
		for p in predictions:
			print(p)
		
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
	main(train=False, predict=True, model_name='GBPUSD_3600_60_20200101_.h5')