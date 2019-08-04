"""
NOTES
- observe training data folder structure & file naming
- params: option to get batch params

"""

print("-- SLTM Neural Network: Forex training and testing environment.")

from AIFX_common_DEV import *

file_namer = FileNaming()

from statistics import stdev

# VARIABLES
data_root_dir = r'/home/jhp/Dukascopy/'
data_file     = r'GBPUSD_20190617-20190717_3600.csv'
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

	
def main(train=False, save=True, predict=True, plot=False, model_name='GBPUSD_3600_60_40.h5'):
	
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
		perc_diff = []
		
		real_prev = predict_data[0]
		
		d_len = sum(1 for x in X_pred)
		for n in range(d_len):
			_X = X_pred[n]
			_X = np.reshape(_X, (_X.shape[1], _X.shape[0], 1))
			
			pred = sc.inverse_transform(NeuralNet.predict(_X))[0][0]
			real = sc.inverse_transform([[y_pred[n]]])[0][0]
			
			if n != 0:
				pred_diff = np.float32(pred) - np.float32(real_prev)
				if pred_diff > 0:
					profit_margin = pred_diff - 0.00046
					if profit_margin > 0 and profit_margin > 0.0009:
						print(real_prev, pred, profit_margin)
				elif pred_diff < 0:
					profit_margin = pred_diff + 0.00046
					if profit_margin < 0 and profit_margin < -0.0009:
						print(real_prev, pred, profit_margin)
					
				real_prev = real
			
			#real_vals.append(real)
			#pred_vals.append(pred)
			#perc_diff.append(real - pred)
			
		#print('min =', min(perc_diff))
		#print('ave =', sum(p_diff for p_diff in perc_diff) / sum(1 for p in perc_diff))
		#print('max =', max(perc_diff))
		#print('dev =', stdev(perc_diff))
		
		if plot:
			plot_prediction(_path="testing/results/graphs/GBPUSD_3600_60_2018-19_10yr.png", 
							timestep=timestep, 
							window=window, 
							real_values=real_vals, 
							pred_values=pred_vals, 
							title="GBPUSD 2018-19", 
							y_label="Price", 
							x_label="Time")

	
if __name__ == '__main__':
	main()