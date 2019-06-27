from csv import reader, writer
from datetime import datetime
from os import listdir, path
from sys import argv, exit


data_root_dir = r'..\data'

if len(argv) > 3:
	try:
		root_path = argv[1]
		timestep  = int(argv[2])
		currency  = argv[3]
	except Exception:
		print('Exit - incorrect timestep.')
		exit()
else:
	print('Exit - too few inputs specified.')
	exit()

def process_raw_data(csv_r, csv_w):
	# Read-write algorithm for parsing tick-by-tick data into a timestep-consistent data series.
	# csv_r: reader object for csv file (data input).
	# csv_w: writer object for csv file (data output).
	
	r0 = next(csv_r)
	t0 = datetime.strptime(r0[1], "%Y%m%d %H:%M:%S.%f").replace(microsecond=0,second=0,minute=0)
	p0 = float(r0[2])
	csv_w.writerow([t0, p0, 0])

	for r in csv_r:
		t1 = datetime.strptime(r[1], "%Y%m%d %H:%M:%S.%f")
		dt = (t1 - t0).seconds
		if dt >= timestep:
			n_timesteps = int(dt / timestep)
			for n in range(n_timesteps - 1):
				csv_w.writerow([t0, p0, 0])
			td = t1.replace(microsecond=0,second=0,minute=0) # round the time down to the hour to keep timestep consistent
			p1 = float(r[2]) 
			csv_w.writerow([td, p1, (t1 - td).seconds]) # log the time difference between the time price was taken at and the previous hour for post-analysis
			t0, p0 = td, p1
	
def format_month(src, dst=''):
	if dst == '':
		dst = src.replace(".csv","") + "_%ds.csv" % timestep

	with open(src, 'r') as csv_1:
		csv_r = reader(csv_1)

		with open(data_root_dir + '\\' + dst, 'w') as csv_2:
			csv_w = writer(csv_2, lineterminator='\r')

			process_raw_data(csv_r, csv_w)
					
def format_year(src, dst=''):
	return

def format_AT(root_path, timestep, currency):
	# format all time

	dst = data_root_dir + '\\' + currency + '_%d' % timestep + '.csv'

	if path.exists(dst):
		while True:
			inst = input('Dataset already exists. Continue? [Y/n]: ')
			if inst == 'n':
				return
			elif inst == 'Y':
				break
	
	print(datetime.now())
		
	with open(dst, 'w') as csv_2:
		csv_w = writer(csv_2, lineterminator='\r')
		
		for year in listdir(root_path):
			for month in listdir(root_path + '\\' + year):
				print(root_path + '\\' + year + '\\' + month)
				
				with open(root_path + '\\' + year + '\\' + month, 'r') as csv_f:
					csv_r = reader(csv_f)
					
					process_raw_data(csv_r, csv_w)
							
							
def main():

	format_AT(root_path, timestep, currency)
	
	return
	
	
if __name__ == '__main__':
	main()