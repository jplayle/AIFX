"""
NOTES
- observe training data folder structure & file naming
- params: option to get batch params

"""

print("-- SLTM Neural Network: Forex training and testing environment.")

from AIFX_common_DEV import *

file_namer = FileNaming()
metrics    = Metrics()

from statistics import stdev

# VARIABLES
data_root_dir = r'/home/jhp/Git/AIFX/dev_env/training_data'
data_file     = r'/GBPUSD_20180731-20190731_86400.csv'
training_data_src = data_root_dir + data_file
data_timestep = extract_training_set_timestep(data_file)

batch_test = False
param_file_path = ''

params = {'timestep':    data_timestep,
		  'window':      10,
		  'increment':   1,
		  'val_split':   0.05,
		  'deep_layers': 0,
		  'units':       80,
		  'dropout':     0.2,
		  'epochs':      1000,
		  'batch_size':  32,
		  'loss_algo':   'mse',
		  'optimizer_algo': 'adam'
		 }

	
def main(train=False, save=True, predict=True, plot=True, model_name='dev_models/GBPUSD_86400_10_20190901_0.h5'):
	
	timestep = params['timestep']
	window   = params['window']
	
	sc = MinMaxScaler(feature_range=(0,1))
	
	NeuralNet = None
	
	if train:
		training_data    = get_data(training_data_src, price_index=1, headers=True)
		td_scaled        = sc.fit_transform(training_data)
		X_train, y_train = shape_data(td_scaled, window, params['increment'])

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
			model_name = file_namer.model_filename(epic='GBPUSD', params=params, valid_till='')
			NeuralNet.save(model_name)

	if predict:
		if model_name:
			NeuralNet = load_model(model_name)
		elif not NeuralNet:
			return
		
		if not train:
			predict_data   = get_data(training_data_src, price_index=1, headers=True)
			pd_scaled      = sc.fit_transform(predict_data)
			X_pred, y_pred = shape_data(pd_scaled, window, params['increment'])
		else:
			X_pred, y_pred = X_train, y_train
		
		real_vals = []
		pred_vals = []
		pred_diff = []
		
		real_prev = sc.inverse_transform([[y_pred[0]]])[0][0]
		
		d_len = sum(1 for x in X_pred) - 1
		for n in range(d_len):
			_X = X_pred[n]
			_X = np.reshape(_X, (_X.shape[1], _X.shape[0], 1))
			
			pred = sc.inverse_transform(NeuralNet.predict(_X))[0][0]
			real = sc.inverse_transform([[y_pred[n]]])[0][0]
			
			if n < d_len:
				#metrics.profit_margin(_pred=pred, _real_prev=real_prev, _ave_mag_diff=0.0009)	
				real_prev = real
	
			real_vals.append(real)
			pred_vals.append(pred)
			pred_diff.append(real - pred)
			
		print('min =', min(pred_diff))
		print('ave =', sum(p_diff for p_diff in pred_diff) / sum(1 for p in pred_diff))
		print('max =', max(pred_diff))
		print('dev =', stdev(pred_diff))
		
		if plot:
			plot_prediction(_path="model_data/graphs/GBPUSD_86400_10_2018-19_1yr.png", 
							timestep=timestep, 
							window=window, 
							real_values=real_vals, 
							pred_values=pred_vals[1:], 
							title="GBPUSD 2018-19", 
							y_label="Price", 
							x_label="Time")

	
if __name__ == '__main__':
	main()