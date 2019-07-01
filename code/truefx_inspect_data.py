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
- correct week change identification algorithm

"""

if len(argv) >= 2:
	try:
		root_path = argv[1]
		#currency  = argv[2]
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
		
		if (tn - t0).days >= 1:
			
		
		if dn != d0:
			d_diff = dn - d0
			if dn == 6 and d0 != 4: #it's a new week but friday was missing
				days_awol += d_diff - 2
				#awol_list.append([])
				t0 = tn
				d0 = dn
				continue
			elif dn != 6 and d_diff > 1:
				days_awol += d_diff - 1
			d0 = dn
			
		tgap = (tn - t0).seconds
		if tgap > max_tgap:
			max_tgap = tgap
			
		t0 = tn
	
	return [days_awol, max_tgap, tn]
	
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
	print(str(datetime.now())[:-7])
	
	for year in listdir(root_path):
		for x, month in enumerate(listdir(root_path + '/' + year)):
			fpath = root_path + '/' + year + '/' + month
			with open(fpath, 'r') as csv_f:
				if x == 0:
					result = inspect_days(list(reader(csv_f)))
				else:
					result = inspect_days(list(reader(csv_f)))#, prev_dt=t0)
				t0 = result[2]
				print(month, result[0], result[1])
							
							
def main():

	#inspect_month(root_path)
	inspect_AT(root_path)
	
	return
	
	
if __name__ == '__main__':
	main()