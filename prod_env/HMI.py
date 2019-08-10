import csv
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import style
from time import (clock, sleep, time)
from datetime import datetime, timedelta
#from datetime import time as dt_time
#from os import listdir
#import email
#import numpy as np

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
			
			with open(fpath + '/' + data_file) as csv_f:
				csv_r = list(reader(csv_f))[::-1]
				csv_r.pop(-1)
				
				for r in range(nrows - len_d):
					try:
						data_row = csv_r[r]
						prices.append(float(data_row[self.pred_data_index]))
						times.append(datetime.strptime(data_row[1], '%Y-%m-%d %H:%M:%S'))
						len_d += 1
					except IndexError:
						return (times, prices)
					except ValueError:
						continue
		
		return (times, prices)
		
	def graphical_display(self, real_lim=0, pred_lim=0, n_stdev=1):
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
				t_prev  = t_now
				
				for epic_ccy, timestep_dict in self.model_store.items():
					if not timestep_dict:
						continue
					#fig       = plt.figure(self.target_epics.index(epic)+1)
					max_tstep = 0
					
					for timestep, model_dict in timestep_dict.items():
						ave_err   = float(model_dict['err_ave']) 
						stdev_err = float(model_dict['err_stdev'])
						if timestep > max_tstep:
							max_tstep = timestep
					
					nrows_historic = int(max_tstep / self.data_interval_sec)
					
					X_hist, Y_hist = self.get_real_plot_data(epic_ccy, nrows=nrows_historic)
					
					plt.plot(X_hist, Y_hist)
					plt.show()
					


			
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

	HMI.graphical_display()

	
if __name__	== '__main__':
	main()