import pandas as pd
from pandas import DataFrame
import matplotlib.pyplot as plt
from matplotlib import style
from time import clock
import pickle

#DEFINE TARGET EPICS AND MODELS FOR PREDICTION
target_epics = ["GBPUSD","EURYEN"]
available_models = ['3600','7200']
pred_rate = 60

while True:

    if clock() % pred_rate == 0:

        for epic in target_epics:
            
            style.use('seaborn')
            fig = plt.figure(target_epics.index(epic)+1)
            ax1 = fig.add_subplot(1,1,1)
            
            #PLOT HISTORIC DATA
            df = pd.read_csv(epic+'_Historic.txt', sep='\t', index_col = "DATETIME", parse_dates=True)
            ax1.plot(df, label = 'Historic Data')
                        
            #PLOT PREDICTED DATA
            for model in available_models:
                df = pd.read_csv(epic + '_' + model + '.txt', sep='\t', index_col = "DATETIME", parse_dates=True)
                ax1.plot(df, label = str(int(model)/3600) + ' Hour Timestep')
            
            #FORMAT PLOT
            ax1.legend()
            plt.title(epic)
            plt.xlabel('Time')
            plt.ylabel('Price')   
            
            #SAVE PLOT LIVE
            plt.savefig(epic+'.png') 
            pickle.dump(ax1, open(epic+'.pickle', "wb"))
            plt.clf()