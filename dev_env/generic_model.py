"""
NOTES
- observe training data folder structure & file naming
- params: option to get batch params

"""

print("-- SLTM Neural Network: Forex training and testing environment.")

from AIFX_common_DEV import *

file_names = FileNaming()
metrics    = Metrics()

from statistics import stdev

# Data Directories
dir1 = '/home/jhp/Git/AIFX/dev_env/training_data/'
dir2 = '/home/jhp/Dukascopy/GBPUSD/'
dir3 = 'training_data/Dukascopy/GBPUSD/'

dir4 = '../prod_env/historic_data/GBPUSD/'

# VARIABLES
data_root_dir = dir3
data_file     = 'GBPUSD_20140717-20190717_86400.csv'
training_data_src = data_root_dir + data_file
data_timestep = extract_training_set_timestep(data_file)

pred_data_path = 'C:/Git/AIFX/prod_env/historic_data/GBPUSD/'
pred_data_file = '/'
pred_data_src  = pred_data_path + pred_data_file

m1 = 'dev_models/GBPUSD_7200_60__4.h5'

batch_test = False
param_file_path = ''

params = {'timestep':    data_timestep,
		  'window':      10,
		  'increment':   1,
		  'val_split':   0.05,
		  'deep_layers': 0,
		  'units':       128,
		  'dropout':     0.2,
		  'epochs':      200,
		  'batch_size':  32,
		  'loss_algo':   'mse',
		  'optimizer_algo': 'adam',
		  'is_stateful':    True
		 }
		 
		 
def forward_test(model_name, hist_data_path, t_start, t_interval=60):
	"""
	Function for testing a model's performance on future data pulled from prod_env.
	- model_name: path to .h5 file of the model to be tested.
	- timestep: in seconds.
	- window: (aka 'look back') - length of input array for prediction.
	- hist_data_path: path to prod_env historic data.
	- t_inerval: time in seconds between each data point 
	"""
	def get_end_time(_hist_data_path):
		end_data_file = sorted(listdir(_hist_data_path))[-1]
		with open(_hist_data_path + end_data_file, 'r') as csv_f:
			csv_r = list(reader(csv_f))
			return datetime.strptime(csv_r[-1][1], '%Y-%m-%d %H:%M:%S')
		
	model = load_model(model_name)
	
	model.reset_states()
			
	params   = file_names.extract_model_params(model_name)
	timestep = int(params['timestep'])
	window   = int(params['window'])

	t_now = t_start
	t_end = get_end_time(hist_data_path) + timedelta(seconds=t_interval)
	
	real_vals = []
	pred_vals = []
	pred_diff = []

	while t_now <= t_end:
		pred_time  = t_now + timedelta(seconds=timestep)

		sc = MinMaxScaler(feature_range=(0,1))
		
		window_data, y_real = build_window_data(hist_data_path, timestep, window, t_now, pred_time)
		
		if window_data != [] and y_real != 0:
			window_data = sc.fit_transform(window_data)
			window_data = np.reshape(window_data, (window_data.shape[1], window_data.shape[0], 1))
			
			y_pred = model.predict(window_data)
			y_pred = sc.inverse_transform(y_pred)[0][0]
			
			real_vals.append(y_real)
			pred_vals.append(y_pred)
			pred_diff.append(abs(y_real - y_pred))
			
			#print(pred_time, y_real, y_pred)
			
		t_now += timedelta(seconds=timestep)
		
	dev_diff = stdev(pred_diff)
		
	print('min =', min(pred_diff))
	print('ave =', sum(p_diff for p_diff in pred_diff) / sum(1 for p in pred_diff))
	print('max =', max(pred_diff))
	print('dev =', dev_diff)
	
	plot_prediction(timestep=timestep, 
					window=window, 
					real_values=real_vals, 
					pred_values=pred_vals, 
					title="GBPUSD "+str(timestep), 
					y_label="Price", 
					x_label="Time")
	
	return dev_diff

	
def main(train=True, save=True, predict=False, fwd_test=True, plot=True, model_name=''):

	timestep = params['timestep']
	window   = params['window']
	
	is_stateful = params['is_stateful']
	
	sc = MinMaxScaler(feature_range=(0,1))
	
	NeuralNet = None
	
	if train:
		training_data    = get_data(training_data_src, price_index=1, headers=True)
		td_scaled        = sc.fit_transform(training_data)
		X_train, y_train = shape_data(td_scaled, window, params['increment'], is_stateful)
		
		if not is_stateful:
			in_shape = (X_train.shape[1], 1)
		else:
			in_shape = (1, X_train.shape[1], 1)

		NeuralNet = LSTM_RNN(in_shape   =in_shape,
							 deep_layers=params['deep_layers'],
							 units      =params['units'],       
							 dropout    =params['dropout'],
							 loss_algo  =params['loss_algo'],
							 optimizer_algo=params['optimizer_algo'],
							 is_stateful   =params['is_stateful']
							 )

		loss_hist = LossHistory()
		time_hist = TimeHistory()

		if not is_stateful:
			hist = NeuralNet.fit(X_train, y_train,                     
								 validation_split=params['val_split'], 
								 epochs          =params['epochs'],              
								 batch_size      =params['batch_size'],          
								 callbacks       =[loss_hist, time_hist], shuffle=False)
		else:
			epochs = params['epochs']
			epochs_str = str(epochs)
			for e in range(epochs):
				print(str(e+1) + "/" + epochs_str)
				NeuralNet.fit(X_train, y_train, epochs=1, batch_size=1, shuffle=False, validation_split=params['val_split'])
				NeuralNet.reset_states()

	if predict:
		if model_name:
			NeuralNet = load_model(model_name)
		elif not NeuralNet:
			return
		
		if not train:
			predict_data   = get_data(pred_data_src, price_index=1, headers=True)
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
	
			real_vals.append(real)
			pred_vals.append(pred)
			pred_diff.append(real - pred)
			
			if n < d_len:
				#metrics.profit_margin(_pred=pred, _real_prev=real_prev, _ave_mag_diff=0.0009)	
				real_prev = real
			
		print('min =', min(pred_diff))
		print('ave =', sum(p_diff for p_diff in pred_diff) / sum(1 for p in pred_diff))
		print('max =', max(pred_diff))
		print('dev =', stdev(pred_diff))
		
		if plot:
			plot_prediction(timestep=timestep, 
							window=window, 
							real_values=real_vals, 
							pred_values=pred_vals, 
							title="GBPUSD", 
							y_label="Price", 
							x_label="Time")
			
	if fwd_test:
		dev_diff = forward_test(model_name, dir4, t_start=datetime(2019, 7, 18, 0, 0, 0))
	else:
		dev_diff = r'0#0'
		
	if save:
		valid_till = input('Enter a valid till date in format "YYYYMMDD":')
		model_name = file_names.model_filename(epic_ccy='GBPUSD', params=params, stdev_diff=dev_diff, valid_till=valid_till)
		NeuralNet.save(model_name)

	
if __name__ == '__main__':
	main()