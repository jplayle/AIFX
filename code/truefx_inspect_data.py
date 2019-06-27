from csv import reader, writer
from datetime import datetime
from os import listdir, path
from sys import argv, exit


root_dir_out = r'..\data\inspection'

"""
To Check (each day):
- Day of week
- Consecutive to previous day
- Start and finish time
- Biggest time gap

"""

if len(argv) > 3:
	try:
		root_path = argv[1]
		currency  = argv[2]
	except Exception:
		print('Exit - incorrect timestep.')
		exit()
else:
	print('Exit - too few inputs specified.')
	exit()

def inspect_raw_data(csv_r, csv_w):
	# Read-write algorithm for inspecting data
	# csv_r: list object from csv file (data input).
	# csv_w: writer object for csv file (data output).
	
	weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

	r0 = next(csv_r)
	
	d_start   = datetime.strptime(r0[1], "%Y%m%d %H:%M:%S.%f")
	d_start_i = t0.weekday()
	max_tgap  = 0
	t1        = d_start # t1 is time on previous loop (needs to be accessible)

	for r in csv_r:
		tn =  datetime.strptime(r0[1], "%Y%m%d %H:%M:%S.%f")
		
		if (tn - d_start).days >= 1:
			d_end  = t1
			d_cons = tn.weekday() - d_start_i 
			
			csv_w.writerow([weekdays[d_start_i], d_cons, d_start, d_end, max_tgap])
			
			d_start   = tn
			d_start_i = tn.weekday()
			max_tgap  = 0
			t1        = tn
			continue
		
		if (tn - t1).seconds > max_tgap:
			max_tgap = (tn - t1).seconds 
			
		t1 = tn
		
		# need to handle last row 
	
def inspect_month(src, dst=''):
	if dst == '':
		dst = src.replace(".csv","") + "_%ds.csv" % timestep

	with open(src, 'r') as csv_1:
		csv_r = reader(csv_1)

		with open(data_root_dir + '\\' + dst, 'w') as csv_2:
			csv_w = writer(csv_2, lineterminator='\r')

			inspect_raw_data(csv_r, csv_w)
					


def inspect_AT(root_path, currency):
	# format all time

	dst = root_dir_out + '\\' + currency + '_inspection.csv'

	if path.exists(dst):
		while True:
			inst = input('Inspection already exists. Continue? [Y/n]: ')
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
					
					inspect_raw_data(csv_r, csv_w)
							
							
def main():

	format_AT(root_path, currency)
	
	return
	
	
if __name__ == '__main__':
	main()