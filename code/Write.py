from datetime import datetime, timedelta, date
from datetime import time as dt_time
import csv

MARKET_epics = [\
                "CS.D.GBPUSD.CFD.IP", "CS.D.USDJPY.CFD.IP", "CS.D.EURGBP.CFD.IP", "CS.D.EURJPY.CFD.IP", "CS.D.EURUSD.CFD.IP", "CS.D.GBPJPY.CFD.IP", \
                "CS.D.AUDJPY.CFD.IP", "CS.D.AUDUSD.CFD.IP", "CS.D.AUDCAD.CFD.IP", "CS.D.USDCAD.CFD.IP", "CS.D.NZDUSD.CFD.IP", "CS.D.NZDJPY.CFD.IP", \
                "CS.D.AUDEUR.CFD.IP", "CS.D.AUDGBP.CFD.IP", "CS.D.CADJPY.CFD.IP", "CS.D.NZDGBP.CFD.IP", "CS.D.NZDEUR.CFD.IP", "CS.D.NZDCAD.CFD.IP"]
Pairs = {}
targ_fields  = ["BID_OPEN", "BID_HIGH", "BID_LOW", "BID_CLOSE", "LTV"]

for epic in MARKET_epics:
    if epic[5:11] not in Pairs:
        Pairs[epic[5:11]]={"BID_OPEN":0,"BID_HIGH":0,"BID_LOW":0,"BID_CLOSE":0,"LTV":0}

#When implementing into master script make below changes:
#self.updates_t_array[epic][‘CURR’]=datetime.today()
#self.epic_data_array = Pairs
        
today = date.today()
idx = (today.weekday() + 1) % 7
sun = str(today - timedelta(idx))

for pair in Pairs:
    with open(pair+"-"+sun+".csv", "w") as file:
        w = csv.writer(file)
        headers = [pair,"Date&Time"]+targ_fields
        w.writerow(headers)
        
        row = [pair]+[datetime.today()]
        for field in Pairs[pair]:
            row = row+[Pairs[pair][field]]
        w.writerow(row)
        
        
