from csv import reader
from datetime import datetime

fpath = r'/home/jhp/Downloads/GBPUSD_Candlestick_1_Hour_BID_01.01.2009-16.07.2019.csv'

with open(fpath, 'r') as csv_f:
	csv_r = reader(csv_f)
	
	header = csv_r.__next__()
	r0     = csv_r.__next__()
	
	p_prev = float(r0[1])
	t_prev = datetime.strptime(r0[0], "%d.%m.%Y %H:%M:%S.%f")
	
	pd = []
	
	for r in csv_r:
		t_curr = datetime.strptime(r[0], "%d.%m.%Y %H:%M:%S.%f")
		p_curr = float(r[1])
		
		t_diff = (t_curr - t_prev).total_seconds()
		
		if t_diff > 3600:
			continue
		
		pd.append(round(((p_prev-p_curr)/p_prev)*100, 5))
			
		t_prev = t_curr
		p_prev = p_curr
	
print(min(pd))
print(sum(p for p in pd) / sum(1 for p in pd))
print(max(pd))