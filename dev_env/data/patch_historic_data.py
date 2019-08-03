from csv import reader, writer

targ_fields = ['openPrice', 'highPrice', 'lowPrice', 'closePrice']

with open('GBPUSD_patch.txt', 'r') as f:
	file = f.read().replace('null', 'None')
	data = eval(file)
	
	with open('GBPUSD_patch.csv', 'a') as csv_f:
		csv_w = writer(csv_f, lineterminator='\n')
		for data_array in data['prices']:
			csv_w.writerow([data_array['snapshotTime'].replace('/', '-')] + [data_array[field] for field in targ_fields] + [data_array['lastTradedVolume']])