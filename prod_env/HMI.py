from sys import argv

#import pandas as pd
import pickle

import matplotlib.pyplot as plt
from matplotlib import style
from matplotlib.widgets import Cursor

from time import (clock, sleep, time)
from datetime import datetime, timedelta
from gc import collect as collect_garbage

from AIFX_common_PROD import *
	

class HumanMachineInterface(AIFX_Prod_Variables):
	
	def __init__(self):
		AIFX_Prod_Variables.__init__(self)
		
		AIFX_Prod_Variables.load_models(self)
		
		self.arg_vals = {'epic':          '',
						't_now':          (datetime.utcnow() - timedelta(seconds=self.data_interval_sec)).replace(second=0, microsecond=0),
						'max_pred_time':   1e12,
						'n_sigma':         1.8, 
						'historic_tsteps': []
						}
		
	def get_real_plot_data(self, _epic_ccy, dt_start, dt_end):
		
		fpath = self.data_dir + _epic_ccy
		
		times  = []
		prices = []
		
		for data_file in sorted(listdir(fpath)):
			
			with open(fpath + '/' + data_file, 'r') as csv_f:
				csv_r = reader(csv_f)
				csv_r.__next__() #remove headers
				
				for data_row in csv_r:
					dt = datetime.strptime(data_row[1], '%Y-%m-%d %H:%M:%S')
					if dt > dt_start and dt <= dt_end:
						try:
							prices.append(float(data_row[self.pred_data_index]))
							times.append(dt)
						except IndexError:
							break
						except ValueError:
							continue
					elif dt > dt_end:
						return (times, prices)
						
		return (times, prices)
	
	def get_pred_plot_data(self, _epic_ccy, _timestep, dt_start, dt_end=None, _stdev_err=0, _n_stdev=1):
		
		if not dt_end:
			dt_end = dt_start + timedelta(seconds=_timestep)
			print(_timestep, dt_start, dt_end)
		
		fpath = self.output_dir + _epic_ccy
		
		times  = []
		prices = []
		u_band = []
		l_band = []
		
		upper_tol = (_stdev_err * _n_stdev)  # + _ave_err
		lower_tol = - (_stdev_err * _n_stdev)# + _ave_err
		
		data_files = []
		
		for file in listdir(fpath):
			file_params = file.split('_')
			
			file_tstep = int(file_params[-1].replace('.csv', ''))
			if file_tstep == _timestep:
				data_files.append(file)
					
		data_files = sorted(data_files)
		
		for df in data_files:
			with open(fpath + '/' + df, 'r') as csv_f:
				csv_r = reader(csv_f)
				for data_row in csv_r:
					dt = datetime.strptime(data_row[0], '%Y-%m-%d %H:%M:%S')
					if dt > dt_start and dt <= dt_end:
						try:
							price = float(data_row[1])
							prices.append(price)
							u_band.append(price + upper_tol)
							l_band.append(price + lower_tol)

							times.append(dt)
						except IndexError:
							break
						except ValueError:
							continue
					elif dt > dt_end:
						return (times, prices, u_band, l_band, dt_end)
		
		return (times, prices, u_band, l_band, dt_end)
	
	def int_to_RGB(self, integer):
		""" Takes an integer value and converts it to a tuple of floats representing an RGB colour value. """
		blue  = (integer & 255) / 255
		green = ((integer >> 8) & 255) / 255
		red   = ((integer >> 16) & 255) / 255
		return (red, green, blue)
		
	def trade_graph(self, _arg_vals):
		"""
		args:
		- epic_ccy
		- t_now
		- max_pred_time
		- n_sigma
		- historic_tsteps
		"""
		style.use('seaborn')
		
		def parse_arg_vals(argvals):
			epic = argvals['epic']
			if not epic:
				return False
			else:
				self.arg_vals['epic'] = epic
			
			for arg, val in argvals.items():
				if arg == 't_now':
					try:
						self.arg_vals[arg] = datetime.strptime(val, '%Y-%m-%d_%H:%M:%S')
					except ValueError:
						return False
						
				elif arg == 'max_pred_time':
					try:
						self.arg_vals[arg] = int(val)
					except ValueError:
						return False
					
				elif arg == 'n_sigma':
					try:
						self.arg_vals[arg] = float(val)
					except ValueError:
						return False
						
				elif arg == 'historic_tsteps':
					try:
						self.arg_vals[arg] = [int(t) for t in list(arg)]
					except ValueError:
						return False
					
			return True
			
		arg_vals_OK = parse_arg_vals(_arg_vals)
		
		if not arg_vals_OK:
			return
		
		epic_ccy = self.arg_vals['epic']
		t_now    = self.arg_vals['t_now']
		
		timestep_dict = self.model_store[epic_ccy]

		ordered_tsteps = sorted([t for t in timestep_dict])
		max_tstep      = ordered_tsteps[-1]
		min_tstep      = ordered_tsteps[0]
			
		hist_data_tstart = t_now - timedelta(seconds=max_tstep)
		pred_data_tstart = t_now
		
		colour_vals = {timestep: self.int_to_RGB(timestep) for timestep in ordered_tsteps}

		fig = plt.figure()#target_epics.index(epic)+1)
		ax1 = fig.add_subplot(1,1,1)
		
		historic_tsteps = self.arg_vals['historic_tsteps']
		if historic_tsteps == []:
			historic_tsteps == ordered_tsteps

		for timestep in ordered_tsteps:
			model_dict = timestep_dict[timestep]

			stdev_err = model_dict['err_stdev']
			n_stdev   = self.arg_vals['n_sigma']
			
			colour = colour_vals[timestep]
			
			if timestep in historic_tsteps:
				X_pred, Y_pred, U_pred, L_pred, ignore = self.get_pred_plot_data(epic_ccy, timestep, dt_start=hist_data_tstart, dt_end=t_now, _stdev_err=stdev_err, _n_stdev=n_stdev)
				ax1.plot(X_pred, Y_pred, color=colour, label=str(int(timestep/3600))+" hour model")
				ax1.plot(X_pred, U_pred, linestyle=":", color=colour)
				ax1.plot(X_pred, L_pred, linestyle=":", color=colour)
			
			X_pred, Y_pred, U_pred, L_pred, new_tstart = self.get_pred_plot_data(epic_ccy, timestep, pred_data_tstart, _stdev_err=stdev_err, _n_stdev=n_stdev)
			ax1.plot(X_pred, Y_pred, color=colour, label=str(int(timestep/3600))+" hour model")
			ax1.plot(X_pred, U_pred, linestyle=":", color=colour)
			ax1.plot(X_pred, L_pred, linestyle=":", color=colour)

			pred_data_tstart = new_tstart

		X_hist, Y_hist   = self.get_real_plot_data(epic_ccy, dt_start=hist_data_tstart, dt_end=t_now)
		
		ax1.plot(X_hist, Y_hist, color="red", label="Real")

		#FORMAT PLOT
		plt.legend()
		plt.title(epic_ccy)
		plt.xlabel('Time')
		plt.ylabel('Price')   

		plt.show()

		#SAVE PLOT LIVE
		#pickle.dump(ax1, open(self.output_dir+epic_ccy+'/'+epic_ccy+'_Graph'+'.pickle', "wb"))
		plt.clf()
					
		
		
class Indicators():

	#Currencies to analyse
	crypto_epics = ["CS.D.BITCOIN.CFD.IP", "CS.D.ETHUSD.CFD.IP", "CS.D.LTCUSD.CFD.IP", "CS.D.XRPUSD.CFD.IP"]
	fiat_epics   = ["CS.D.GBPUSD.CFD.IP", "CS.D.USDJPY.CFD.IP", "CS.D.EURGBP.CFD.IP", "CS.D.EURJPY.CFD.IP", "CS.D.EURUSD.CFD.IP", "CS.D.GBPJPY.CFD.IP",	\
					"CS.D.AUDJPY.CFD.IP", "CS.D.AUDUSD.CFD.IP", "CS.D.AUDCAD.CFD.IP", "CS.D.USDCAD.CFD.IP", "CS.D.NZDUSD.CFD.IP", "CS.D.NZDJPY.CFD.IP",	\
					"CS.D.AUDEUR.CFD.IP", "CS.D.AUDGBP.CFD.IP", "CS.D.CADJPY.CFD.IP", "CS.D.NZDGBP.CFD.IP", "CS.D.NZDEUR.CFD.IP", "CS.D.NZDCAD.CFD.IP"]
	target_epics = fiat_epics + crypto_epics
	
	#Indicators to document
	targ_fields  = ["VAL_ERR", "PERC_VAL_ERR", "DELTA_VAL_ERR", "PERC_DELTA_VAL_ERR", "STAND_DEV", "BOXPLOT", "DIRECTION"]
	
	#Read in prediction
	#df = pd.read_csv('pred.csv',sep='\t')

	#Create dataset from whatever columns you are interested in 
	#pred = df[['DATETIME','PRED']]
	
	#Live dataset created in same way as predicted for now, will need to be live updating in future
	#live = df[['DATETIME','LIVE']]
		
	def value_accuracy(self): #Add time values in future (start/end datetime you are interested in)
		#Initialise arrays
		val_err = []
		abs_val_err = []
		perc_err = []
		
		#Check DATETIME is the same in both prediction and live datasets
		for i in self.pred['DATETIME']:
			for j in self.live['DATETIME']:
				if i == j:
		
					#Find difference between predicted and live datsets/ add to array
					val_err = val_err + [self.pred.loc[self.pred['DATETIME'] == i]['PRED'].values[0]-\
					self.live.loc[self.live['DATETIME'] == i]['LIVE'].values[0]]
					
					#Find magnitude of difference between predicted and live datsets/ add to array
					abs_val_err = abs_val_err + [abs(self.pred.loc[self.pred['DATETIME'] == i]['PRED'].values[0]-\
					self.live.loc[self.live['DATETIME'] == i]['LIVE'].values[0])]
					
					#Find magnitude of % difference between predicted and live datsets/ add to array               
					perc_err = perc_err + [100*abs((self.pred.loc[self.pred['DATETIME'] == i]['PRED'].values[0]-\
					self.live.loc[self.live['DATETIME'] == i]['LIVE'].values[0])/\
					self.live.loc[self.live['DATETIME'] == i]['LIVE'].values[0])]
		
		#Calculate indication metrics
		cum_val_err = sum(abs_val_err)
		avg_val_err = cum_val_err/len(val_err)
		cum_perc_err = sum(perc_err)
		avg_perc_err = cum_perc_err/len(perc_err)
		print("Cumulative value error is: " + str(cum_val_err))
		print("Average value error is: " + str(avg_val_err))
		print("Average value percentage error is: " + str(avg_perc_err)+"%")
		plt.plot(perc_err)
		plt.show()
		
	def delta_value_accuracy(self): #Add time values in future (start/end datetime you are interested in)
	
		#Initialise arrays
		val_err = []
		abs_val_err = []
		perc_err = []
		
		#Check DATETIME is the same in both prediction and live datasets
		for i in self.pred['DATETIME']:
			for j in self.live['DATETIME']:
				if i == j:
				
					#Skip first row as there can be no delta with only on value
					if i == self.pred['DATETIME'].min():
						pass
					else:
					
						#Find difference between predicted and live datsets/ add to array
						val_err = val_err + [(self.pred.loc[self.pred['DATETIME'] == i]['PRED'].values[0]-\
						self.pred.loc[self.pred['DATETIME'].shift(-1) == i]['PRED'].values[0])-\
						(self.live.loc[self.live['DATETIME'] == i]['LIVE'].values[0]-\
						self.live.loc[self.live['DATETIME'].shift(-1) == i]['LIVE'].values[0])]
		 
						#Find magnitude of difference between predicted and live datsets/ add to array
						abs_val_err = abs_val_err + [abs((self.pred.loc[self.pred['DATETIME'] == i]['PRED'].values[0]-\
						self.pred.loc[self.pred['DATETIME'].shift(-1) == i]['PRED'].values[0])-\
						(self.live.loc[self.live['DATETIME'] == i]['LIVE'].values[0]-\
						self.live.loc[self.live['DATETIME'].shift(-1) == i]['LIVE'].values[0]))]

						#Check to see if percentage calculation is dividing by 0 
						#NOTE: In such cases % error has been set to 0. need to reconsider in future
						if self.live.loc[self.live['DATETIME'] == i]['LIVE'].values[0]-\
						self.live.loc[self.live['DATETIME'].shift(-1) == i]['LIVE'].values[0]==0:
							perc_err = perc_err + [0]
						else:

							#Find magnitude of % difference between predicted and live datsets/ add to array               
							perc_err = perc_err + [100*abs(((self.pred.loc[self.pred['DATETIME'] == i]['PRED'].values[0]-\
							self.pred.loc[self.pred['DATETIME'].shift(-1) == i]['PRED'].values[0])-\
							(self.live.loc[self.live['DATETIME'] == i]['LIVE'].values[0]-\
							self.live.loc[self.live['DATETIME'].shift(-1) == i]['LIVE'].values[0]))/\
							(self.live.loc[self.live['DATETIME'] == i]['LIVE'].values[0]-\
							self.live.loc[self.live['DATETIME'].shift(-1) == i]['LIVE'].values[0]))]
						
		#Calculate indication metrics
		cum_val_err = sum(abs_val_err)
		avg_val_err = cum_val_err/len(val_err)
		cum_perc_err = sum(perc_err)
		avg_perc_err = cum_perc_err/len(perc_err)
		print("Cumulative delta value error is: " + str(cum_val_err))
		print("Average delta value error is: " + str(avg_val_err))
		print("Average delta percentage error is: " + str(avg_perc_err)+"%")
		plt.plot(perc_err)
		plt.show()
		
	   
		
def main():

	HMI = HumanMachineInterface()
	
	arg_vals = {'epic': ''}
	
	for argval_pair in argv[1:]:
		arg, val      = argval_pair.split('=')
		arg_vals[arg] = val

	HMI.trade_graph(arg_vals)

	
if __name__	== '__main__':
	main()