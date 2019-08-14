import pandas as pd
import pickle

import matplotlib.pyplot as plt
from matplotlib import style
from matplotlib.widgets import Cursor

from time import (clock, sleep, time)
from datetime import datetime, timedelta

from AIFX_common_PROD import *

class HumanMachineInterface(AIFX_Prod_Variables):
	
	def __init__(self):
		AIFX_Prod_Variables.__init__(self)
		
		AIFX_Prod_Variables.load_models(self)
		
	def get_real_plot_data(self, _epic_ccy, nrows=1):
		
		fpath = self.data_dir + _epic_ccy
		
		times  = []
		prices = []
		len_d  = 0
		
		for data_file in sorted(listdir(fpath))[::-1]:
			
			with open(fpath + '/' + data_file, 'r') as csv_f:
				csv_r = list(reader(csv_f))[::-1]
				csv_r.pop(-1)
				
				for r in range(nrows - len_d):
					try:
						data_row = csv_r[r]
						
						prices.append(float(data_row[self.pred_data_index]))
						times.append(datetime.strptime(data_row[1], '%Y-%m-%d %H:%M:%S'))
						
						len_d += 1
					except IndexError:
						break
					except ValueError:
						continue
		
		return (times[::-1], prices[::-1])
	
	def get_pred_plot_data(self, _epic_ccy, _timestep, dt_start, dt_end=None, _ave_err=0, _stdev_err=0, _n_stdev=1):
		
		if not dt_end:
			dt_end = dt_start + timedelta(seconds=_timestep)
		
		fpath = self.output_dir + _epic_ccy
		
		times  = []
		prices = []
		u_band = []
		l_band = []
		len_d  = 0
		
		upper_tol = (_stdev_err * _n_stdev)  # + _ave_err
		lower_tol = - (_stdev_err * _n_stdev)# + _ave_err
		
		data_files = []
		
		for file in listdir(fpath):
			file_params = file.split('_')
			
			file_year  = int(file_params[1])
			file_month = int(file_params[2])
			
			if file_year == dt_start.year and file_month == dt_start.month:
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

							len_d += 1
						except IndexError:
							break
						except ValueError:
							continue
		
		return (times[::-1], prices[::-1], u_band[::-1], l_band[::-1], dt_end)
	
	def int_to_RGB(self, integer):
		""" Takes an integer value and converts it to a tuple of floats representing an RGB colour value. """
		blue  = (integer & 255) / 255
		green = ((integer >> 8) & 255) / 255
		red   = ((integer >> 16) & 255) / 255
		return (red, green, blue)
		
	def graphical_display_service(self, real_lim=0, pred_lim=0, n_stdev=1):
		"""
		End goal:
		- plot up to max timestep into the future
		- add min & max deviations
		"""
		
		style.use('seaborn')
		
		t_prev = clock()
		
		while True:
			t_now = clock()
			
			if t_now - t_prev >= 10:#self.pred_rate:
				t_prev = t_now
				dt_now = (datetime.utcnow() - timedelta(seconds=self.data_interval_sec)).replace(second=0, microsecond=0)
				
				for epic_ccy, timestep_dict in self.model_store.items():
					if not timestep_dict:
						continue
					
					ordered_tsteps = sorted([t for t in timestep_dict])
					max_tstep      = ordered_tsteps[-1]
					min_tstep      = ordered_tsteps[0]
					
					pred_data_tstart = datetime.strptime('2019-08-09 20:57:00', '%Y-%m-%d %H:%M:%S') - timedelta(seconds=max_tstep)
					pred_data_t_end  = datetime.strptime('2019-08-09 20:57:00', '%Y-%m-%d %H:%M:%S') + timedelta(seconds=min_tstep)
					
					colour_vals = {timestep: self.int_to_RGB(timestep) for timestep in ordered_tsteps}
					
					fig = plt.figure()#target_epics.index(epic)+1)
					ax1 = fig.add_subplot(1,1,1)
					
					for timestep in ordered_tsteps:
						model_dict = timestep_dict[timestep]
						
						ave_err   = float(model_dict['err_ave']) 
						stdev_err = float(model_dict['err_stdev'])
						
						if timestep == min_tstep:
							X_pred, Y_pred, U_pred, L_pred, new_tstart = self.get_pred_plot_data(epic_ccy, timestep, pred_data_tstart, dt_end=pred_data_t_end, _ave_err=ave_err, _stdev_err=stdev_err, _n_stdev=n_stdev)
						else:
							X_pred, Y_pred, U_pred, L_pred, new_tstart = self.get_pred_plot_data(epic_ccy, timestep, pred_data_tstart, _ave_err=ave_err, _stdev_err=stdev_err, _n_stdev=n_stdev)
							
						colour = colour_vals[timestep]
								   
						ax1.plot(X_pred, Y_pred, color=colour, label=str(int(timestep/3600))+" hour model")
						
						ax1.plot(X_pred, U_pred, linestyle=":", color=colour)#, linewidth="0.5")
						ax1.plot(X_pred, L_pred, linestyle=":", color=colour)#, linewidth="0.5")
						
						pred_data_tstart = new_tstart
						
					nrows_historic = int(max_tstep / self.data_interval_sec)
					
					X_hist, Y_hist   = self.get_real_plot_data(epic_ccy, nrows=nrows_historic)
					
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
		
	   
	# def standard_dev(self)
		# a

	# def boxplot(self)
		# a

	# def direction(self)
		# a

	# def gain_v_loss(self)
		# 
		
def main():

	HMI = HumanMachineInterface()

	HMI.graphical_display_service()

	
if __name__	== '__main__':
	main()