import numpy as np
import matplotlib.pyplot as pyplot

from os import walk, listdir
from sys import argv, exit
from csv import reader, writer
from time import clock
from datetime import datetime, timedelta

from keras.models    import Sequential, load_model
from keras.layers    import Dense
from keras.layers    import LSTM
from keras.layers    import TimeDistributed
from keras.layers    import Dropout
from keras.callbacks import Callback

from sklearn.preprocessing import MinMaxScaler


class FileNaming():
	
	def __init__(self):
		self.project_root    = '../'
		self.models_root     = 'dev_models/'
		self.graphs_root     = 'model_data/graphs/'
		
		self.field_seperator = '_'
	
	def get_uid(self, ftype, check_str):
		uid = -1
		for _dir in walk(self.project_root):
			if '.git' in _dir:
				continue
			for f in _dir[2]:
				if f[-3:] == ftype:
					f_mainbody = self.field_seperator.join(f.split(self.field_seperator)[:-1])
					if check_str == f_mainbody:
						uid += 1
						
		return str(uid + 1)
	
	def model_filename(self, epic, params, valid_till=''):
		suffix = '.h5'
		
		fields = []
		fields.append(str(params['timestep']))
		fields.append(str(params['window']))
		#fields.append(str(ave_diff).replace('.', '#'))
		#fields.append(str(stdev_diff).replace('.', '#'))
		fields.append(str(valid_till))
		
		fname_main = self.field_seperator.join([epic] + fields)
		fname_uid  = self.get_uid(suffix, fname_main)
		
		fname = self.field_seperator.join([fname_main, fname_uid]) + suffix
		
		return self.models_root + fname
		
	def extract_model_params(self, model_fname):
		model_fname = model_fname[::-1]
		model_fname = model_fname[:model_fname.find('/')]
		model_fname = model_fname[:model_fname.find('\\')]
		model_params = model_fname.split(self.field_seperator)
		return {'epic_ccy': model_params[0], 'timestep': model_params[1], 'window': model_params[2], 'valid_till': model_params[3].replace('.h5', '')}
	
	def graph_filename(self, suffix):
		
		return
		
	

class Metrics():

	def profit_margin(_pred, _real_prev, _ave_mag_diff, min_margin=0.0009, min_mag_diff=0, max_mag_diff=0):
	
		pred_diff = np.float32(pred) - np.float32(real_prev)
		
		if pred_diff > 0:
			profit_margin = pred_diff - ave_mag_diff
			if profit_margin > 0 and profit_margin > min_margin:
				print(real_prev, pred, profit_margin)
				
		elif pred_diff < 0:
			profit_margin = pred_diff + ave_mag_diff
			if profit_margin < 0 and profit_margin < -min_margin:
				print(real_prev, pred, profit_margin)
		
		
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
			
def get_data(src, price_index=1, headers=False):
	# src: relative path to .csv file containing data.
	# Return type: list, data is strings as found in csv.
	with open(src, 'r') as csv_f:
		csv_r = reader(csv_f)
		if headers:
			csv_r.__next__()
		return [[r[price_index]] for r in csv_r]
	
def shape_data(data, window=5, increment=1, is_stateful=False):
	# data:      numpy ndarray of normalised/scaled data points for training on.
	# window:    integer - number of previous data points to use per prediction. 
	# increment: integer - how many timesteps to shift the window each time.
	# is_stateful: whether to build data array compatible for stateful predictions
	if is_stateful:
		increment = window
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
	
def build_window_data(self, data_path, timestep=0, window=0, t_start=None):
	"""
	- open relevant epic data file
	- return a list of prices at timestep intervals of length=window
	- remove ability to return none
	"""
	
	if data_path[-1] != '/':
		data_path += '/'
	
	def search_around_blank(data_list, index, r_skip, newf_search=False, _x_prev=0):
		#search for nearby data within +/-x% of timestep e.g. +/- 3 mins
		new_file = False
		
		data_offset = int(r_skip * self.max_data_offset)
		if not newf_search:
			search_rng = (1, data_offset + 1)
		else:
			search_rng = (0, data_offset - _x_prev)
		
		for x in range(search_rng[0], search_rng[1]):
			try:
				data_up = data_list[index + x][2]
				if data_up != '':
					return data_up
			except IndexError:
				pass
				
			try:
				data_dwn = data_list[index - x][2]
				if data_dwn != '':
					return data_dwn
			except IndexError:
				return ['newf', x]
				
		return ''
	
	window_data = []
	
	row_skip = int(timestep / 60)
	
	data_files = sorted(listdir(data_path))[::-1]
	
	w_len       = 0
	r_skip_newf = 0 #row skip if opening a new file
	srch_newf   = False
	x_prev      = 0
	
	initiate = True
	
	for data_file in data_files:

		with open(data_path + data_file, 'r') as csv_f:
			csv_r = list(reader(csv_f))
			csv_r.pop(0) #remove headers
			
			j = 0
			if initiate:
				for r in csv_r[::-1]:
					break
					data_time = datetime.strptime(r[1], '%Y-%m-%d %H:%M:%S')
					if data_time == t_start:
						r_skip_newf = j
						initiate    = False
						break
					elif data_time < t_start:
						return []
					j += 1
			if initiate:
				continue

			if srch_newf:
				srch_newf  = False
				data_point = search_around_blank(csv_r, -1, row_skip, newf_search=True, _x_prev=x_prev)
				try:
					float(data_point)
					window_data.append([data_point])
					w_len += 1
					if w_len == window:
						return window_data[::-1]
				except ValueError:
						return []
		
			for x in range(window - w_len):					
				i = -((x * row_skip) + r_skip_newf) - 1

				try:
					data_point = csv_r[i][2]
					if data_point == '':
						data_point = search_around_blank(csv_r, i, row_skip)
					try:
						float(data_point)
						window_data.append([data_point])
						w_len += 1
						if w_len == window:
							return window_data[::-1]
					except ValueError:
						if data_point != '':
							srch_newf   = True
							x_prev      = data_point[1]
							r_skip_newf = sum(-1 for r in csv_r) - i - 1 + row_skip
							break
						else:
							return []
							
				except IndexError:
					r_skip_newf = sum(-1 for r in csv_r) - i - 1
					break
					
	if w_len == window:				
		return window_data[::-1]
	else:
		return []
	
def LSTM_RNN(in_shape, deep_layers=0, units=80, dropout=0.2, loss_algo='mse', optimizer_algo='adam', is_stateful=False):
	
	if deep_layers > 0:
		return_seq = True
	else:
		return_seq = False

	regressor = Sequential()

	if is_stateful:
		regressor.add(LSTM(units=units, stateful=is_stateful, return_sequences=return_seq, batch_input_shape=in_shape))
	else:
		regressor.add(LSTM(units=units, stateful=is_stateful, return_sequences=return_seq, input_shape=in_shape))
	regressor.add(Dropout(dropout))
	
	for l in range(deep_layers):
		if l == deep_layers - 1:
			regressor.add(LSTM(units=units, return_sequences=False))
		else:
			regressor.add(LSTM(units=units, return_sequences=return_seq))
		regressor.add(Dropout(dropout))

	regressor.add(Dense(units=1))

	regressor.compile(optimizer=optimizer_algo, loss=loss_algo)
	
	return regressor
	
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

			
def plot_prediction(timestep, window, real_values=[], pred_values=[], title="", y_label="", x_label="", path=''):
	#len_rv = len(real_values)
	#len_pv = pred_values.size
	pyplot.plot(real_values)#, [x * timestep for x in range(len_rv)])
	pyplot.plot(pred_values, linestyle='-.')#, [window + (x * timestep) for x in range(len_pv)])
	
	#pyplot.axis([0, timestep*len_rv, min(min(real_values), min(pred_values)), max(max(real_values), max(pred_values))])
	pyplot.title(title)
	pyplot.ylabel(y_label)
	pyplot.xlabel(x_label)
	pyplot.legend(['Real', 'Predicted'], loc='upper right')
	
	pyplot.show()
	
	if path:
		pyplot.savefig(_path)