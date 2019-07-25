from csv import reader, writer
from datetime import datetime, date, time, timedelta
from os import listdir, path
from sys import argv, exit

root_dir_out = r'..\data\inspection'

"""
Dev
- cmd line
"""

"""
Notes
- Open  = column 3
- Close = column 6

"""

if len(argv) >= 2:
	try:
		file_path = argv[1]
		currency  = argv[2]
	except Exception:
		currency = ''
else:
	print('Exit - too few inputs specified.')
	exit()
	
	
weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
days_map = {6:6, 0:5, 1:4, 2:3, 3:2, 4:1}
	
	
def inspect(csv_r, prev_dt=''):
	# Check for continuity of days only
	# key assumption: in no case is an entire week (or more) missing
	
	def extract_datetime(date_str, time_str):
		date_ = date(int(date_str[:4]), int(date_str[4:6]), int(date_str[6:8]))
		time_ = time(int(time_str[:2]), int(time_str[2:4]), int(time_str[4:6]))
		dt_   = datetime.combine(date_, time_)
		return [date_, dt_]
	
	csv_r.pop(0) # skip header row
	
	date_time  = extract_datetime(csv_r[0][1], csv_r[0][2])
	date_0, t0 = date_time[0], date_time[1]
	open_0, c0 = float(csv_r[0][3]), float(csv_r[0][6])
	
		
	csv_r.pop(0)
	l_row = sum(1 for r in csv_r)
	
	days_awol = 0
	awol_list = []
	max_tgap  = 0
	occ_tgap  = []
	awol      = False
	
	for r in csv_r:
			
		date_time  = extract_datetime(r[1], r[2])
		date_n, tn = date_time[0], date_time[1]
		open_n, cn = float(r[3]), float(r[6])
		
		d_diff = (date_n - date_0).days
		if d_diff > 1:
			for d in range(d_diff-1):
				bd = date_0 + timedelta(days=d+1)
				if bd.weekday() != 5:
					awol = True
					days_awol += 1
					#awol_list.append(bd)
			if awol:
				#print(' | '.join([str(i) for i in [t0, tn, c0, open_n]]))
				awol = False
			date_0, t0 = date_n, tn
			open_0, c0 = open_n, cn
			continue
			
		tgap = (tn - t0).seconds
		if tgap > 3600:
			print(tgap)
			max_tgap = tgap
			occ_tgap = [t0, tn]
			
		date_0, t0 = date_n, tn
		open_0, c0 = open_n, cn
		
	return [days_awol, max_tgap, occ_tgap, awol_list]
					
def inspect_AT(file_path, currency=''):
	# format all time
	"""
	dst = root_dir_out + '\\' + currency + '_inspection.csv'
	if path.exists(dst):
		while True:
			inst = input('Inspection already exists. Continue? [Y/n]: ')
			if inst == 'n':
				return
			elif inst == 'Y':
				break
	"""
	print('START TIME:', str(datetime.now())[:-7])
	
	with open(file_path, 'r') as csv_f:
		result = inspect(list(reader(csv_f)))
		print(result[1], result[2])
							
							
def main():

	#inspect_month(root_path)
	inspect_AT(file_path, currency)
	
	return
	
	
if __name__ == '__main__':
	main()