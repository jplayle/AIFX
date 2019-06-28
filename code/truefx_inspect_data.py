from csv import reader, writer
from datetime import datetime, date
from os import listdir, path
from sys import argv, exit


root_dir_out = r'..\data\inspection'

"""
Unit of continuation - 1 week, checks performed:
- Start day, end (DONE)
- All days present? (DONE)
- Biggest time gap & when it occurred (DONE)

Dev
- 
- Handle end of file

"""

if len(argv) == 3:
	try:
		root_path = argv[1]
		currency  = argv[2]
	except Exception:
		print('Exit - incorrect timestep.')
		exit()
else:
	print('Exit - too few inputs specified.')
	exit()

def inspect_raw_data(csv_r, csv_w, prev_dt=''):
	# Read-write algorithm for inspecting data
	# csv_r: list object from csv file (data input).
	# csv_w: writer object for csv file (data output).
	
	weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
	
	if prev_dt == '':
		w_t0 = datetime.strptime(csv_r[0][1], "%Y%m%d %H:%M:%S.%f")
	else:
		w_t0 = prev_dt
		
	w_start_d = w_t0.weekday()
	max_tgap  = 0
	tgap_occ  = w_t0
	t1        = w_t0
	d_present = [w_start_d]
	days_map  = {6:6, 0:5, 1:4, 2:3, 3:2, 4:1}
		
	csv_r.pop(0)
	l_row = sum(1 for r in csv_r)
	
	for x, r in enumerate(csv_r):
		
		if x == l_row:
			return datetime.strptime(r[1], "%Y%m%d %H:%M:%S.%f")
			
		tn = datetime.strptime(r[1], "%Y%m%d %H:%M:%S.%f")
		print(tn.isocalender())
		dn = tn.weekday()
		
		if dn >= w_start_d:
			if dn == 6 or (tn - w_t0).days / days_map[w_start_d] >= 1: # check if a sunday or later
				d_missing = days_map[w_start_d] - len(d_present)
				result    = [weekdays[w_start_d], weekdays[dn], d_missing, max_tgap, tgap_occ]
				print(result)
				csv_w.writerow(result)
				w_t0      = tn
				w_start_d = dn
				max_tgap  = 0
				tgap_occ  = w_t0
				t1        = w_t0
				d_present = [w_start_d]
				continue
			
		if dn not in d_present:
			d_present.append(dn)
		
		tgap = (tn - t1).seconds
		if tgap > max_tgap:
			max_tgap = tgap 
			tgap_occ = t1
			
		t1 = tn
		
		# need to handle last row 
	
def inspect_month(src, dst=''):
	
	dst = root_dir_out + '\\' + currency + '_inspection.csv'

	if path.exists(dst):
		while True:
			inst = input('Inspection already exists. Continue? [Y/n]: ')
			if inst == 'n':
				return
			elif inst == 'Y':
				break

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
					csv_r = list(reader(csv_f))
					
					inspect_raw_data(csv_r, csv_w)
							
							
def main():

	inspect_AT(root_path, currency)
	
	return
	
	
if __name__ == '__main__':
	main()