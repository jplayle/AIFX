from csv import reader, writer
from datetime import datetime
from os import listdir
from sys import argv, exit

data_root_dir = r'..\data'

print(argv)
if len(argv) > 2:
	try:
		path     = argv[1]
		timestep = int(argv[2])
	except Exception:
		print('Exit - incorrect timestep.')
		exit()
else:
	print('Exit - no file/folder specified.')
	exit()

src = r"GBPUSD-2016-11.csv"

timestep = 5 #s


def format_month(src, dst=''):
	if dst == '':
		dst = src.replace(".csv","") + "_%ds.csv" % timestep

	with open(src, 'r') as csv_1:
		csv_r = reader(csv_1)

		with open(dst, 'w') as csv_2:
			csv_w = writer(csv_2, lineterminator='\r')

			r0 = next(csv_r)
			t0 = datetime.strptime(r0[1], "%Y%m%d %H:%M:%S.%f")
			p0 = float(r0[2])

			for r in csv_r:
				t1 = datetime.strptime(r[1], "%Y%m%d %H:%M:%S.%f")
				dt = (t1 - t0).seconds
				if dt >= timestep:
					n_timesteps = int(dt / timestep)
					for n in range(n_timesteps):
						csv_w.writerow([p0])
					t0 = t1
					p0 = float(r[2])
					
def format_year(src, dst=''):
	return

def format_dataset(currency, dst=''):
	return

	if dst == '':
		dst = src.replace(".csv","") + "_%ds.csv" % timestep
		
	with open(dst, 'w') as csv_2:
		csv_w = writer(csv_2, lineterminator='\r')
		
		for year in listdir(currency):
			for month in listidr(currency + '\\' + year):
				with open(currency + '\\' + year + '\\' + month, 'r') as csv_f:
					csv_r = reader(csv_f)
					
					r0 = next(csv_r)
					t0 = datetime.strptime(r0[1], "%Y%m%d %H:%M:%S.%f")
					p0 = float(r0[2])

					for r in csv_r:
						t1 = datetime.strptime(r[1], "%Y%m%d %H:%M:%S.%f")
						dt = (t1 - t0).seconds
						if dt >= timestep:
							n_timesteps = int(dt / timestep)
							for n in range(n_timesteps):
								csv_w.writerow([p0])
							t0 = t1
							p0 = float(r[2])
					