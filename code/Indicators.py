import csv
import pandas as pd
#import numpy as np

class Indicators():

    #Read in prediction
    df = pd.read_csv('pred.csv',sep='\t')

    #Create dataset from whatever columns you are interested in 
    pred = df[['DATETIME','PRED']]
    
    #Live dataset created in same way as predicted for now, will need to be live updating in future
    live = df[['DATETIME','LIVE']]
        
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
       
    # def standard_dev(self)
        # a

    # def boxplot(self)
        # a

    # def direction(self)
        # a

    # def gain_v_loss(self)
        # 
def main():

    indicators = Indicators()

    indicators.value_accuracy()
    
    indicators.delta_value_accuracy()

main()