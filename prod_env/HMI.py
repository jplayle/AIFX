import csv
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import style
from time import (clock, sleep, time)
from datetime import datetime, timedelta
#from datetime import time as dt_time
from os import listdir
#import email
#import numpy as np

from AIFX_common_PROD import *


class HumanMachineInterface(AIFX_Prod_Variables):
    
    def __init__(self):
        AIFX_Prod_Variables.__init__(self)
		
	def graphical_display(self, stationary=True, fwd_limit=None):
		
		style.use('seaborn')
		
		t_prev = clock()
		
		while True:
			t_now = clock()
			
    		if t_now - t_prev >= self.pred_rate:
				
				for epic in self.target_epics:
					fig = plt.figure(target_epics.index(epic)+1)
					ax1 = fig.add_subplot(1,1,1)
					
					max_tstep = 0
					
					for model_file in os.listdir(self.model_dir):
						model_params = model_file.split('_')
						
						epic_ccy = model_params[0]
						timestep = int(model_params[1])
						if timestep > max_tstep:
							max_tstep = timestep
						window   = int(model_params[2]) 
						
					nrows_historic = max_tstep / self.data_interval_sec
					
					historic_data_path = self.data_dir + epic_ccy
					historic_data_file = historic_data_path + '/' + sorted(listdir(historic_data_path))[-1]
					df = pd.read_csv(historic_data_file, nrows=nrows_historic, index_col = "DATETIME", parse_dates=True)
            		ax1.plot(df, label = 'Historic Data')
					
				


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
    df = pd.read_csv('pred.csv',sep='\t')

    #Create dataset from whatever columns you are interested in 
    pred = df[['DATETIME','PRED']]
    
    #Live dataset created in same way as predicted for now, will need to be live updating in future
    live = df[['DATETIME','LIVE']]
        
    def startup_sequence(self):
		"""
		1. Check if data files exist and retrieve previous update time from the last row if they do
		2. Write necessary number of blank rows based on difference between previous time from step 1 and the account time now
		3. For each epic data file: set self.updates_t_array[epic]['PREV'] to the last written time from step 2
		- Because of step 3, the writer algorithm will fill in any blank rows that are required between finishing the start-up sequence and writing the first data
		"""
		t_now = datetime.utcnow()
		fname_suffix = "-".join(['', str(t_now.year), str(t_now.month)]) + 'metrics' + '.csv'
		
		for epic in self.target_epics:
			ccy   = epic[5:11] #currency code e.g. EURGBP
			fname = ccy + fname_suffix
			
			if not path.exists(ccy):
				makedirs(ccy)
				
			data_files = sorted(listdir(ccy))

			if fname in data_files:
				latest_file = ccy + '/' + fname 	
				
			elif data_files != []:
				latest_file = ccy + '/' + data_files[-1]
				
			else:
				self.updates_t_array[epic]['PREV'] = t_now - timedelta(minutes=self.interval_val)
				continue
			
			mints = [] #missing intervals
			with open(latest_file, 'r') as csv_rf:
				csv_r = list(reader(csv_rf))
				LUT   = datetime.strptime(csv_r[-1][1], '%Y-%m-%d %H:%M:%S')
				mints = self.handle_tgap(LUT, t_now, epic)
				
			if mints != []:
				data_array = [[ccy, mi] + ['' for field in self.targ_fields] for mi in mints]
				self.updates_t_array[epic]['PREV'] = self.write_data(epic[5:11], data_array)
			else:
				self.updates_t_array[epic]['PREV'] = LUT - timedelta(minutes=self.interval_val)
        
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
        
    def write_data(self, _epic_ccy, _data):
		"""
		- recurrent function: writes data assigning file name based on datetime of update as 'epic-year-month.csv'
		- returns LUT (last update time) so when write_data() is called by startup_sequence() it can be used to set self.updates_t_array[epic]['PREV']
		- schema for _data: [[epic, datetime, BID_OPEN, BID_HIGH, BID_LOW, BID_CLOSE, LTV] * n] where n >= 1
		"""
		row_0  = _data.pop(0)
		t_curr = row_0[1]
		f_year = str(t_curr.year)  #file year
		f_mon  = str(t_curr.month) #file month
		fname  = "-".join([_epic_ccy, f_year, f_mon]) + '.csv'
		
		full_path = _epic_ccy + '/' + fname
		if not path.exists(full_path):
			write_headers = True
		else:
			write_headers = False
		
		LUT = t_curr
		with open(full_path, 'a') as csv_f:
			csv_w = writer(csv_f, lineterminator='\n')
			
			if write_headers:
				csv_w.writerow(['EPIC', 'DATE_TIME'] + self.targ_fields)
			
			csv_w.writerow(row_0)
			
			for r in _data[:]: # [:] ensures that _data is modified in-place by calls to _data.remove()
				t_curr = r[1]
				if str(t_curr.year) != f_year or str(t_curr.month) != f_mon:
					return self.write_data(_epic_ccy, _data)
				else:
					csv_w.writerow(r)
					LUT = t_curr
					_data.remove(r)
					
		return LUT
        
        
    def read_data(self, _epic_ccy, _data):
		"""
		- recurrent function: writes data assigning file name based on datetime of update as 'epic-year-month.csv'
		- returns LUT (last update time) so when write_data() is called by startup_sequence() it can be used to set self.updates_t_array[epic]['PREV']
		- schema for _data: [[epic, datetime, BID_OPEN, BID_HIGH, BID_LOW, BID_CLOSE, LTV] * n] where n >= 1
		"""
		row_0  = _data.pop(0)
		t_curr = row_0[1]
		f_year = str(t_curr.year)  #file year
		f_mon  = str(t_curr.month) #file month
		fname  = "-".join([_epic_ccy, f_year, f_mon]) + '.csv'
		
		full_path = _epic_ccy + '/' + fname
		if not path.exists(full_path):
			write_headers = True
		else:
			write_headers = False
		
		LUT = t_curr
		with open(full_path, 'a') as csv_f:
			csv_w = writer(csv_f, lineterminator='\n')
			
			if write_headers:
				csv_w.writerow(['EPIC', 'DATE_TIME'] + self.targ_fields)
			
			csv_w.writerow(row_0)
			
			for r in _data[:]: # [:] ensures that _data is modified in-place by calls to _data.remove()
				t_curr = r[1]
				if str(t_curr.year) != f_year or str(t_curr.month) != f_mon:
					return self.write_data(_epic_ccy, _data)
				else:
					csv_w.writerow(r)
					LUT = t_curr
					_data.remove(r)
					
		return LUT
            
        
def main():

    indicators = Indicators()

    indicators.value_accuracy()
    
    indicators.delta_value_accuracy()

    
if __name__	== '__main__':
	main()