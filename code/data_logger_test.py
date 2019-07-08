import csv

MARKET_epics = [\
                "CS.D.GBPUSD.CFD.IP", "CS.D.USDJPY.CFD.IP", "CS.D.EURGBP.CFD.IP", "CS.D.EURJPY.CFD.IP", "CS.D.EURUSD.CFD.IP", "CS.D.GBPJPY.CFD.IP", \
                "CS.D.AUDJPY.CFD.IP", "CS.D.AUDUSD.CFD.IP", "CS.D.AUDCAD.CFD.IP", "CS.D.USDCAD.CFD.IP", "CS.D.NZDUSD.CFD.IP", "CS.D.NZDJPY.CFD.IP", \
                "CS.D.AUDEUR.CFD.IP", "CS.D.AUDGBP.CFD.IP", "CS.D.CADJPY.CFD.IP", "CS.D.NZDGBP.CFD.IP", "CS.D.NZDEUR.CFD.IP", "CS.D.NZDCAD.CFD.IP"]
Pairs = {}

#while True:
for epic in MARKET_epics:
    if epic[5:11] not in Pairs:
        Pairs[epic[5:11]+" BID"] = {}
        Pairs[epic[5:11]+" OFR"] = {}
        Pairs[epic[5:11]+" LTP"] = {}
        
with open('test.csv', "w", newline='') as csv_file:
    writer = csv.DictWriter(csv_file,fieldnames=Pairs.keys())  
    writer.writeheader()
    
    for i in range(1,10):
        Pairs['GBPUSD BID']=i    
        writer.writerow(Pairs)
            
print(Pairs)

