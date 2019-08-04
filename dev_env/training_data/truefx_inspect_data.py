from csv import reader, writer
from datetime import datetime, date, timedelta
from os import listdir, path
from sys import argv, exit


root_dir_out = r'..\data\inspection'

"""
Unit of continuation - 1 week, checks performed:
- Start day, end (DONE)
- All days present? (DONE)
- Biggest time gap & when it occurred (DONE)
Dev
- correct week change identification algorithm
"""

if len(argv) >= 2:
	try:
		root_path = argv[1]
		currency  = argv[2]
	except Exception:
		exit()
else:
	print('Exit - too few inputs specified.')
	exit()
	
def inspect_days(csv_r, prev_dt=''):
	# Check for continuity of days only
	# key assumption: in no case is an entire week (or more) missing
	
	weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
	days_map = {6:6, 0:5, 1:4, 2:3, 3:2, 4:1}
	
	if prev_dt == '':
		t0 = datetime.strptime(csv_r[0][1], "%Y%m%d %H:%M:%S.%f")
		date_0 = date(int(csv_r[1][1][:4]), int(csv_r[1][1][4:6]), int(csv_r[1][1][6:8]))
	else:
		t0 = prev_dt
		
	csv_r.pop(0)
	l_row = sum(1 for r in csv_r)
	
	d0        = t0.weekday()
	days_awol = 0
	awol_list = []
	max_tgap  = 0
	
	for r in csv_r:
			
		tn = datetime.strptime(r[1], "%Y%m%d %H:%M:%S.%f")
		dn = tn.weekday()
		
		date_n = date(int(r[1][:4]), int(r[1][4:6]), int(r[1][6:8]))
		
		d_diff = (date_n - date_0).days
		if d_diff > 1:
			for d in range(d_diff-1):
				bd = date_0 + timedelta(days=d+1)
				if bd.weekday() != 5:
					days_awol += 1
					awol_list.append(bd)
			t0     = tn
			date_0 = date_n
			continue
			
		tgap = (tn - t0).seconds
		if tgap > max_tgap:
			max_tgap = tgap
			
		t0     = tn
		date_0 = date_n
		
	return [days_awol, max_tgap, tn, awol_list]
	
def inspect_month(src, dst=''):
	"""
	dst = root_dir_out + '\\' + currency + '_inspection.csv'
	if path.exists(dst):
		while True:
			inst = raw_input('Inspection already exists. Continue? [Y/n]: ')
			if inst == 'n':
				return
			elif inst == 'Y':
				break
	"""
	with open(src, 'r') as csv_1:
		result = inspect_days(list(reader(csv_1)))
		print(src, result[0], result[1])
					
def inspect_AT(root_path, currency=''):
	# format all time
	
	dst = root_dir_out + '\\' + currency + '_inspection.csv'
	if path.exists(dst):
		while True:
			inst = raw_input('Inspection already exists. Continue? [Y/n]: ')
			if inst == 'n':
				return
			elif inst == 'Y':
				break
	
	print('START TIME: ', str(datetime.now())[:-7])
	
	with open(dst, 'w') as csv_wf:
		csv_w = writer(csv_wf, lineterminator='\n')
		for year in listdir(root_path):
			for x, month in enumerate(listdir(root_path + '/' + year)):
				fpath = root_path + '/' + year + '/' + month
				with open(fpath, 'r') as csv_f:
					if x == 0:
						result = inspect_days(list(reader(csv_f)))
					else:
						result = inspect_days(list(reader(csv_f)))#, prev_dt=t0)
					t0  = result[2]
					row = [month, result[0], result[1]] + [awol_date for awol_date in result[3]] 
					csv_w.writerow(row)
							
							
def main():

	#inspect_month(root_path)
	inspect_AT(root_path, currency)
	
	return
	
	
if __name__ == '__main__':
	main()