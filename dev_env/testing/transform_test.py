import numpy as np

from sys import argv, exit
from csv import reader, writer
from time import clock

from sklearn.preprocessing import MinMaxScaler

# VARIABLES
training_data_src = r"../data/GBPUSD-2016-09_5s.csv"
validate_data_src = r"../data/GBPUSD-2016-10_5s.csv"
predict_data_dst  = r""

window = 60
		
def get_data(src):
	with open(src, 'r') as csv_f:
		csv_r = reader(csv_f)
		return [r for r in csv_r]


def log_results(path='', mode='a', results=[]):
	#results: array of lists where each list is a row to be written. 
	with open(path, mode) as csv_f:
		csv_w = writer(csv_f, lineterminator='\n')
		for r in results:
			csv_w.writerow([r])
			
def main():

	sc = MinMaxScaler(feature_range=(0,1))

	training_data = get_data(training_data_src)
	validate_data = get_data(validate_data_src)
	
	sc.fit(training_data + validate_data)

	training_data_scaled = sc.transform(training_data)
	validate_data_scaled = sc.transform(validate_data)
	
	td2 = sc.inverse_transform(training_data_scaled)
	vd2 = sc.inverse_transform(validate_data_scaled)
	
	td2_diff = [td2[x][0] - float(training_data[x][0]) for x in range(len(training_data))]
	vd2_diff = [vd2[x][0] - float(validate_data[x][0]) for x in range(len(validate_data))]
	
	log_results('td_fit.csv', 'a', results=td2_diff)
	log_results('vd_fit.csv', 'a', results=vd2_diff)
	
	
if __name__ == '__main__':
	main()