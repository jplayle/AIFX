from csv import reader, writer
from datetime import datetime
#from math import floor
#from time import clock

src = r"GBPUSD-2016-11.csv"

timestep = 5 #s


dst = src.replace(".csv","") + "_%ds.csv" % timestep
print(dst)

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