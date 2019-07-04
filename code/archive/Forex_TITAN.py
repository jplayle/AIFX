# ----------------------------------------------------------------------- #
#                            Forex T.I.T.A.N.                             #   
#            Technical Indicator Trading of an Autonomous Nature          #
#             Developed by Josh Playle - joshplayle@hotmail.com           #
#                              Broker - IG                                #
# ----------------------------------------------------------------------- #


# Nerve centre
from dateutil.relativedelta import (relativedelta, FR)
from queue import (Queue, LifoQueue, Empty, Full)
from requests.exceptions import RequestException
from requests import (get, put, post, delete)
from collections import OrderedDict
from urllib.request import urlopen
from urllib.parse import urlencode
from csv import (reader, writer)
import matplotlib.pyplot as plt
from time import (clock, sleep)
from os import (path, makedirs)
from datetime import datetime
from math import (sqrt, ceil)
from calendar import weekday
from threading import Thread
from getpass import getpass
from json import dumps
from sys import exit
import numpy as np
import logging


# Deforestation
def __init__logs():

    global error_logger
    global info_logger
    global trade_logger
    global CC_logger

    formatter1 = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    formatter2 = logging.Formatter('%(asctime)s , %(levelname)s , %(message)s')

    error_logger = logging.getLogger('error_log')
    error_logger.setLevel(logging.DEBUG)
    error_handler = logging.FileHandler(r"C:\Users\Josh\Documents\Forex\Logs\Error Log.log")
    error_handler.setFormatter(formatter1)
    error_logger.addHandler(error_handler)

    info_logger = logging.getLogger('info_log')
    info_logger.setLevel(logging.INFO)
    info_handler = logging.FileHandler(r"C:\Users\Josh\Documents\Forex\Logs\Info Log.log")
    info_handler.setFormatter(formatter1)
    info_logger.addHandler(info_handler)

    trade_logger = logging.getLogger('trade_log')
    trade_logger.setLevel(logging.INFO)
    trade_handler = logging.FileHandler(r"C:\Users\Josh\Documents\Forex\Logs\Trade Log.csv")
    trade_handler.setFormatter(formatter2)
    trade_logger.addHandler(trade_handler)

    CC_logger = logging.getLogger('CC_log')
    CC_logger.setLevel(logging.DEBUG)
    CC_handler = logging.FileHandler(r"C:\Users\Josh\Documents\Forex\Logs\CCs.csv")
    CC_handler.setFormatter(formatter2)
    CC_logger.addHandler(CC_handler)

__init__logs()

class Log():

    def __init__(self, log_q):
        self.log_q = log_q
        self.blah = 0

    def logging_service(self):
        while True:
            try:
                msg = self.log_q.get(block=False)
            except Empty:
                continue 

            if msg[0] == 'trade':
                print('\n\ntrade logging triggered\n\n')
                tkt = msg[1]
                trade_logger.info('%d, , 0, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s', r.status_code, tkt['epic'], tkt['inst'], tkt['dealReference'], \
                                tkt['dealId'], tkt['status'], tkt['reason'], tkt['dealStatus'], tkt['level'], tkt['size'], tkt['direction'], tkt['stopLevel'], \
                                tkt['limitLevel'], tkt['profit'])

            elif msg[0] == 'position error':
                tkt = msg[1]
                trade_logger.debug('%d, %s, 0, , %s, , %s', tkt['statusCode'], tkt['rbody'], tkt['inst'], tkt['dealId'])

            elif msg[0] == 'confirmation error':
                tkt = msg[1]
                trade_logger.debug('%d, %s, 0, , %s, %s', tkt['statusCode'], tkt['rbody'], tkt['inst'], tkt['dealRef'])

    def run(self):
        self.log_thread = Thread(target=self.logging_service, daemon=True)
        self.log_thread.start()


# Pen Spins
def STD(c):
    #Takes a list of prices of type ndarray and calculates the standard deviation.
    try:
        sigma = round(sqrt(np.mean((c - c.mean())**2)), 5)
    except MemoryError as e:
        error_logger.exception('Memory Error - %s', e)
        sigma = 0
    return sigma

def CC(a, b):
    #Takes two lists of prices of type ndarray and calculates the correlation coefficient between them.
    try:
        cc = round(np.sum((a - a.mean()) * (b - b.mean())) / sqrt(np.sum((a - a.mean())**2) * np.sum((b - b.mean())**2)), 5)
    except MemoryError as e:
        error_logger.exception('Memory Error - %s', e)
        cc = 0
    return cc


# A Bridge Too Far
StatArb_Q    = Queue(maxsize=1)
Message_Q    = Queue()
Trade_Status = Queue()
Live_Pairs   = Queue()
Log_Q        = Queue()
Sy_Q         = Queue()
Plot_Q       = Queue()
in_limbo     = True


# Smoke Signals
class IG_API():

    def __init__(self, msg_q, status_q, log_q, sy_q, live=False, ATD=300):
        global XST
        global CST
        global client_ID
        global LS_addr

        self.msg_q = msg_q
        self.status_q = status_q
        self.log_q = log_q
        self.sy_q = sy_q
        self.ave_trade_duration = ATD # (initial guess)

        # set up variables for DEMO or PROD:
        if live == False:
            self.r00t = "https://demo-api.ig.com/gateway/deal"
            self.IG_API_key = "50a4f4f776e8c06cd19c8c486f191c1f63b411b6"
            self.username = "ForexTITAN"
            self.password = "H0unds101"
        elif live == True:
            self.r00t = "https://api.ig.com/gateway/deal"
            self.API_Key = ""
            self.username = input("Enter username: ")
            self.password = getpass("Enter password: ")

    def login(self):
        global XST
        global CST
        global client_ID
        global LS_addr
        #Setup initial log in details:
        self.headers = {
            'Content-Type': 'application/json; charset=UTF-8',
            'Accept': 'application/json; charset=UTF-8',
            'VERSION': '1',
            'X-IG-API-KEY': self.IG_API_key
            }
        self.creds = dumps({
            'identifier': self.username,
            'password': self.password
            })

        #Send the post request to log in:
        while True:
            try:
                r = post(self.r00t + "/session", headers=self.headers, data=self.creds)
                if r.status_code == 200:
                    logging.info('Log in to IG - %d %s', r.status_code, r.text)
                break
            except RequestException:
                sleep(10)
                continue


        #Obtain security tokens & client ID:
        CST = str(r.headers['CST'])
        XST = str(r.headers['X-SECURITY-TOKEN'])
        client_ID = str(r.text[r.text.find("clientId")+11 : r.text.find("clientId")+20])

        #Update request authentication details:
        self.headers = {
            'Content-Type': 'application/json; charset=UTF-8',
            'Accept': 'application/json; charset=UTF-8',
            'VERSION': '1',
            'X-IG-API-KEY': self.IG_API_key,
            'X-SECURITY-TOKEN': XST,
            'CST': CST
            }

        #Obtain the URL for the Lighstreamer server:
        txt = r.text
        s0 = txt.find('lightstreamerEndpoint',0)
        s1 = txt.find(':',s0) + 2
        s2 = txt.find('"',s1)
        LS_addr = txt[s1:s2]

    def create_position(self, params={}):
        disconnected = False
        open_parameters = dumps(params)

        try:
            r = post(self.r00t + '/positions/otc', headers=self.headers, data=open_parameters)
            open_ticket = eval(r.text)
            open_dealRef = open_ticket['dealReference']

        except RequestException:
            disconnected = True
            open_dealRef = ""
            sleep(1)

        except SyntaxError:
            self.log_q.put(['position error', {'statusCode': r.status_code, 'rbody': r.text, 'epic': eval(open_parameters)['epic'], 'inst': 'open'}])
            open_dealRef = ""

        except KeyError:
            self.log_q.put(['position error', {'statusCode': r.status_code, 'rbody': r.text, 'epic': eval(open_parameters)['epic'], 'inst': 'open'}])
            open_dealRef = ""
        
        if disconnected:
            error_logger.debug('Connection Error - Create Position')

        return open_dealRef #DEPRECIATED - MOVED TO STAT-ARB LOOP

    def close_position(self, params={}):
        disconnected = False
        close_parameters = dumps(params)

        close_headers = self.headers
        close_headers['_method'] = "DELETE"

        while True:
            try:
                r = post(self.r00t + '/positions/otc', headers=close_headers, data=close_parameters)
                close_ticket = eval(r.text)
                close_dealRef = close_ticket['dealReference']
                break

            except RequestException:
                disconnected = True
                close_dealRef = ""
                while True:
                    if clock() - self.trade_start_time <= self.ave_trade_duration:
                        continue
                    else:
                        break
                    break

            except SyntaxError:
                self.log_q.put(['position error', {'statusCode': r.status_code, 'rbody': r.text, 'epic': eval(close_parameters)['epic'], 'inst': 'close'}])
                close_dealRef = ""
                break

            except KeyError:
                self.log_q.put(['position error', {'statusCode': r.status_code, 'rbody': r.text, 'dealId': eval(close_parameters)['dealId'], 'inst': 'close'}])
                close_dealRef = ""
                break

        if disconnected:
            error_logger.debug('Connection Error - Close Position')

        return close_dealRef #DEPRECIATED - MOVED TO STAT-ARB LOOP

    def confirmation(self, dealRef, type):
        try:
            r = get(self.r00t + '/confirms/' + dealRef, headers=self.headers)
            ct = r.text.replace("null", '""').replace("true", '"True"').replace("false", '"False"')
        except RequestException:
            error_logger.debug('Connection Error - no confirmation for trade %s', dealRef)
            tkt = {}
            return tkt

        try:
            tkt = eval(ct)
            tkt['inst'] = type
            tkt['statusCode'] = r.status_code
            self.log_q.put(['trade', tkt])
        except SyntaxError:
            self.log_q.put(['confirmation error', {'statusCode': r.status_code, 'rbody': r.text, 'inst': type, 'dealRef': dealRef}])
            tkt = {}
        return tkt

    def mail_service(self):
        t0 = 0
        i = 0
        while True:
            t = clock() - t0
            if t >= 3600:
                self.login()
                #self.sy_q.put([self.XST, self.CST, self.LS_addr, self.client_ID])
                t0 = clock()

            try:
                msg = self.msg_q.get(block=False)
            except Empty:
                continue
            info = {}
            
            for l in msg:
                if l[0] == 'create':
                    dealRef = self.create_position(params=l[1])
                    trade_ticket = broker.confirmation(dealRef, 'open')
                    self.trade_start_time = clock()

                    try:
                        info[l[1]['epic']] = [trade_ticket['status'], trade_ticket['dealId']]
                        #trade_logger.info('%s, %s, %s' % (l[1]['epic'], trade_ticket['status'], trade_ticket['dealId']))
                    except KeyError:
                        info[l[1]['epic']] = ["", ""]
                        #trade_logger.info('%s, %s, %s' % (l[1]['epic'], 'key error', 'key error'))

                elif l[0] == 'close':
                    closeRef = self.close_position(params=l[1])
                    trade_ticket = broker.confirmation(closeRef, 'close')

            if msg[0][0] == 'create':
                self.status_q.put(info)

    def run_mail_service(self):
        self.mail_thread = Thread(target=self.mail_service, daemon=True)
        self.mail_thread.start()

    def search(self, keyword):
        try:
            results = get(self.r00t + "/markets?searchTerm=" + keyword, headers=self.headers, data=self.creds).text
        except RequestException:
            results = ""
        return results

    def market_status(self, epic):
        results = get(self.r00t + "/markets/" + epic, headers=self.headers, data=self.creds).text
        results = eval(results.replace("true", "True").replace("false", "False").replace("null", "None"))
        market_state = results['snapshot']['marketStatus']
        return market_state

    def accounts(self):
        try:
            acc = get(self.r00t + "/accounts", headers=self.headers).text
        except RequestException:
            acc = ""
        return acc

    def logout(self):
        for n in range(0,20):
            try:
                end = delete(self.r00t + "/session", headers=self.headers)
                if end.status_code != 200 or 'error' in end.text.lower():
                    print('Error logging out of broker.')
                    print(end.text)
                else:
                    print('Logged out of broker successfully.')
                info_logger.info('Logged out of IG - %d %s', end.status_code, end.text.rstrip())
                break
            except RequestException:
                sleep(30)
                continue

class Lightstreamer():

    connection_path = "/lightstreamer/create_session.txt"
    binding_path    = "/lightstreamer/bind_session.txt"
    control_path    = "/lightstreamer/control.txt"
    keepalive       = "30000"
    data_buffer     = "360000" 

    TT      = 3600
    max_spr = 2

    MARKET_epics = [\
                "CS.D.GBPUSD.CFD.IP", "CS.D.USDJPY.CFD.IP", "CS.D.EURGBP.CFD.IP", "CS.D.EURJPY.CFD.IP", "CS.D.EURUSD.CFD.IP", "CS.D.GBPJPY.CFD.IP", \
                "CS.D.AUDJPY.CFD.IP", "CS.D.AUDUSD.CFD.IP", "CS.D.AUDCAD.CFD.IP", "CS.D.USDCAD.CFD.IP", "CS.D.NZDUSD.CFD.IP", "CS.D.NZDJPY.CFD.IP", \
                "CS.D.AUDEUR.CFD.IP", "CS.D.AUDGBP.CFD.IP", "CS.D.CADJPY.CFD.IP", "CS.D.NZDGBP.CFD.IP", "CS.D.NZDEUR.CFD.IP", "CS.D.NZDCAD.CFD.IP"]
    price_array  = {}
    bid_array    = {}
    spr_array    = {}
    time_array   = []
    TaT_array    = []
    e_trail      = False

    def __init__(self, LS_server_name, LS_pswd, IG_ID, calc_q, live_q, msg_q, log_q, sy_q, plot_q, headers, creds):
        # Comms:
        self.r00t                  = "https://demo-api.ig.com/gateway/deal"
        self.LS_server_name        = LS_server_name
        self.LS_pswd               = LS_pswd
        self.IG_ID                 = IG_ID
        self.headers               = headers
        self.creds                 = creds
        self.connection_parameters = bytes(urlencode({"LS_op2": "create",
                                                      "LS_cid": "mgQkwtwdysogQz2BJ4Ji kOj2Bg",
                                                      "LS_adapter_set": "DEFAULT",
                                                      "LS_user": self.IG_ID,
                                                      "LS_password": self.LS_pswd,
                                                      "LS_keepalive_millis": self.keepalive,
                                                      "LS_content_length": self.data_buffer
                                                      }), 'utf-8')
        # Price database:
        for e in self.MARKET_epics:
            cp = self.current_price(e)
            self.price_array[e] = cp[0]
            self.bid_array[e]   = cp[1]
            sleep(5)
        self.trail_array = {epic: [] for epic in self.MARKET_epics}
        with open('trail_array.csv', 'r') as trail_csv:
            csv_r = reader(trail_csv)
            k = 0
            trail_accepted = False
            for r in csv_r:
                # trail database up-to-dateness:
                if k == 0:
                    k += 1
                    try:
                        t_storage = datetime.strptime(r[0], "%Y-%m-%d %H:%M:%S.%f")
                    except Exception:
                        trail_accepted = False
                        break
                    prev_TT = int(r[1])
                    if float(r[2]) < self.TT:
                        # break if previous session didn't accumulate a full trail
                        trail_accepted = False
                        break
                    # assess time lag since trail stored:
                    if datetime.today().weekday() == '6' and t_storage.weekday() == '4':
                        market_close = datetime.utcnow() + relativedelta(weekday=FR(-1))
                        market_close = market_close.replace(hour=22, minute=0, second=0, microsecond=0)
                        t_lag = ceil((market_close - t_storage).total_seconds())
                    else:
                        t_lag = ceil((datetime.utcnow() - t_storage).total_seconds())
                    if prev_TT > self.TT and t_lag <= (prev_TT * 0.1):
                        self.up_time = self.TT
                        trail_accepted = True
                    elif t_lag <= (self.TT * 0.1):
                        self.up_time = prev_TT + t_lag
                        trail_accepted = True
                    else:
                        self.up_time = 0
                        break
                        # future upgrade: fill in blanks with a price history query
                    continue
                # trail array:
                if trail_accepted:
                    e = 0
                    for p in r:
                        self.trail_array[self.MARKET_epics[e]].append(float(p))
                        e += 1
                else:
                    break
            if len(self.trail_array[self.MARKET_epics[0]]) < 300:
                trail_accepted = False
            # time array:
            if trail_accepted:
                print('Trail accepted.')
                self.trail_array  = {epic: np.array(self.trail_array[epic]) for epic in self.MARKET_epics}
                dt_time_array     = round(self.up_time / len(self.trail_array['CS.D.GBPUSD.CFD.IP']), 2)
                self.time_array   = [t * dt_time_array for t in range(0, len(self.trail_array['CS.D.GBPUSD.CFD.IP']))]
                self.renewal_time = round(prev_TT + t_lag, 2)
            else:
                print('Trail rejected.')
                self.trail_array  = {epic: np.array([]) for epic in self.MARKET_epics}
                self.time_array   = []
                self.renewal_time = 0
                # populate trail from IG price history
            self.downtime = 0
        # Queues:
        self.calc_q   = calc_q
        self.live_q   = live_q
        self.msg_q    = msg_q
        self.log_q    = log_q
        self.sy_q     = sy_q
        self.plot_q   = plot_q
        self.stream_q = Queue()
        # Data streams:
        self.subscription_count = -1
        self.combinations       = self.combo_grid(self.MARKET_epics)
        self.CC_grid            = {}
        self.live_pairs         = []
        self.TaT                = 0
        # Cointegration constants:
        self.m       = 0
        self.c       = 0
        self.y_bar   = 0
        self.x_bar   = 0
        self.trigger = 0
        self.e_ave   = 0

    def current_price(self, epic):
        results = get(self.r00t + "/markets/" + epic, headers=self.headers, data=self.creds).text
        results = eval(results.replace("true", "True").replace("false", "False").replace("null", "None"))
        price = float(results['snapshot']['offer'])
        bid = float(results['snapshot']['bid'])
        return [price, bid]

    def read_stream(self):
        line = self.server_msg.readline().decode().rstrip()
        return line

    def connect(self, keepalive="30000", total_data="360000"):
        session_details = {}
        cmd = ''
        #Setup connection parameters:
        connection_parameters = bytes(urlencode({"LS_op2": "create",
                                                 "LS_cid": "mgQkwtwdysogQz2BJ4Ji kOj2Bg",
                                                 "LS_adapter_set": "DEFAULT",
                                                 "LS_user": self.IG_ID,
                                                 "LS_password": self.LS_pswd,
                                                 "LS_keepalive_millis": keepalive,
                                                 "LS_content_length": total_data
                                                 }), 'utf-8')  
        #Connect to server:
        while True:
            try:
                self.server_msg = urlopen(self.LS_server_name + self.connection_path, connection_parameters)
                cmd = self.read_stream()
                break
            except ConnectionError:
                print('Connection Error when connecting to LS server. Waiting 1...')
                sleep(1)
        #Obtain details of the session parameters:
        if cmd == "OK":
            while True:
                new_line = self.read_stream()
                if new_line:
                    detail_key, detail_value = new_line.split(":",1)
                    session_details[detail_key] = detail_value
                else:
                    break
            self.SessionId = session_details['SessionId']
            self.ControlAddress = "https://" + session_details['ControlAddress']
            self.SessionTime = int(session_details['KeepaliveMillis']) / 100           # convert milliseconds to seconds
            info_logger.info('Connection to LS server.')

    def stream(self, CC_criteria=0.8, visible=False):
        trail_time = self.TT,
        dt_array = np.array([])
        receiving = True
        
        while receiving:
            try:
                pkt = self.read_stream()
            except Exception:
                pkt = 'None'

            if pkt[0].isdigit():
                self.up_time = clock() - self.downtime

                if not self.live_q.empty():
                    self.live_pairs = self.live_q.get()
               
                epic_id = int(pkt[:pkt.find(",")])

                #update the EPIC's price when a new value has arrived:
                l = pkt.split('|')
                #print('uptime:', round(self.up_time, 0), 'subs:', l[1], l[2], end='\r')
                if l[2] != '' and l[2] != '$' and l[2] != '#':
                    self.bid_array[self.MARKET_epics[epic_id]] = float(l[2])
                if l[1] != '' and l[1] != '$' and l[1] != '#':
                    self.price_array[self.MARKET_epics[epic_id]] = float(l[1])
                    self.time_array.append(round(clock(),2))
                else:
                    continue

                #update price trails accordingly:
                TaT =  round(clock() - self.time_array[-len(self.trail_array[self.MARKET_epics[0]])], 2)
                if TaT == trail_time:
                    for id in range(0, len(self.MARKET_epics)):
                        self.trail_array[self.MARKET_epics[id]] = np.append(self.trail_array[self.MARKET_epics[id]], self.price_array[self.MARKET_epics[id]])
                        self.trail_array[self.MARKET_epics[id]] = np.delete(self.trail_array[self.MARKET_epics[id]], 0)
                elif TaT > trail_time:
                    for id in range(0, len(self.MARKET_epics)):
                        self.trail_array[self.MARKET_epics[id]] = np.append(self.trail_array[self.MARKET_epics[id]], self.price_array[self.MARKET_epics[id]])
                        self.trail_array[self.MARKET_epics[id]] = np.delete(self.trail_array[self.MARKET_epics[id]], [0,1])
                else:
                    for id in range(0, len(self.MARKET_epics)):
                        self.trail_array[self.MARKET_epics[id]] = np.append(self.trail_array[self.MARKET_epics[id]], self.price_array[self.MARKET_epics[id]])
                
                #CALCS & COMMS:
                if self.up_time >= trail_time:
                    if self.live_pairs != []:
                        spr_trail = np.absolute(self.trail_array[self.MARKET_epics[j]] - self.trail_array[self.MARKET_epics[p]])
                        spr_STD = STD(spr_trail)
                        STD_j = STD(self.trail_array[self.live_pairs[0]])
                        STD_p = STD(self.trail_array[self.live_pairs[1]])
                        sma = round(np.mean(spr_trail), 5)

                        self.calc_q.put({'epic0': self.live_pairs[0],
                                         'epic1': self.live_pairs[1],
                                         'epic0_ofr': self.price_array[self.live_pairs[0]],
                                         'epic1_ofr': self.price_array[self.live_pairs[1]],
                                         'epic0_bid': self.bid_array[self.live_pairs[0]],
                                         'epic1_bid': self.bid_array[self.live_pairs[1]],
                                         'epic0_std': STD_j,
                                         'epic1_std': STD_p,
                                         'std_d': spr_STD, 'sma': sma})
                    else:
                        #calculate Correlation Coefficients:
                        n = 0
                        CC_max = 0
                        for c in self.combinations:
                            n += 1
                            self.CC_grid[n] = CC(self.trail_array[self.MARKET_epics[c[0]]], self.trail_array[self.MARKET_epics[c[1]]])
                            if self.CC_grid[n] > CC_max:
                                CC_max = self.CC_grid[n]
                                j = c[0]
                                p = c[1]
                        #set live pairs to the highest correlation:
                        if CC_max >= CC_criteria:
                            self.live_pairs.append(self.MARKET_epics[j])
                            self.live_pairs.append(self.MARKET_epics[p])

                            spr_trail = np.absolute(self.trail_array[self.MARKET_epics[j]] - self.trail_array[self.MARKET_epics[p]])
                            spr_STD = STD(spr_trail)
                            STD_j = STD(self.trail_array[self.MARKET_epics[j]])
                            STD_p = STD(self.trail_array[self.MARKET_epics[p]])
                            sma = round(np.mean(spr_trail), 5)
                            self.calc_q.put({'epic0': self.MARKET_epics[j],
                                             'epic1': self.MARKET_epics[p],
                                             'epic0_ofr': self.price_array[self.MARKET_epics[j]],
                                             'epic1_ofr': self.price_array[self.MARKET_epics[p]],
                                             'epic0_bid': self.bid_array[self.MARKET_epics[j]],
                                             'epic1_bid': self.bid_array[self.MARKET_epics[p]],
                                             'epic0_std': STD_j,
                                             'epic1_std': STD_p,
                                             'std_d': spr_STD, 'sma': sma})
            else:
                # Stream Maintenance:
                if pkt == 'None':
                    start_downtime = clock()
                    print("Error receiving updates from the server.")

                    # try to establish a connection unless session time expires
                    while True:
                        try:
                            urlopen('http://www.google.com') # a reliable site that will likely always respond
                            connected = True
                            break
                        except Exception:
                            connected = False

                    # if a connection is present, continue as normal, else reconnect
                    self.connect()
                    self.subscription_count = -1
                    for epic in self.MARKET_epics: #NB: implement capability to pass this to a separate thread
                        self.subscribe(sub="MARKET", epic=epic, field_schema="OFFER BID")

                    self.downtime += clock() - start_downtime
                # Continue receiving if a probe message is received:
                elif pkt == "PROBE":
                    print('probe')
                    z = 1
                    continue
                # Stop receiving if an error message is received:
                elif pkt == "ERROR":
                    print("Error message received.")
                    start_downtime = clock()
                    self.make_safe()
                    self.downtime += clock() - start_downtime
                # Rebind the session if a loop command is received:
                elif pkt == "LOOP":
                    start_downtime = clock()
                    #print("Rebinding session.", clock())
                    self.connect()
                    self.subscription_count = -1
                    for epic in self.MARKET_epics:
                        self.subscribe(sub="MARKET", epic=epic, field_schema="OFFER BID")
                    #info_logger.info('Rebind')
                    self.downtime += clock() - start_downtime
                # Stop receiving and then make-safe session if sync error (bad Session ID) is received: 
                elif pkt == "SYNC ERROR":
                    start_downtime = clock()
                    print("SYNC error encountered. Starting from scratch...\n")
                    self.make_safe()
                    self.downtime += clock() - start_downtime
                # Stop receiving and restart session (if in trading hours) if server ends the stream:
                elif pkt == "END":
                    start_downtime = clock()
                    print("Session ended by server. Restarting session...", clock())
                    self.connect()
                    self.subscription_count = -1
                    for epic in self.MARKET_epics:
                        self.subscribe(sub="MARKET", epic=epic, field_schema="OFFER BID")
                    self.downtime += clock() - start_downtime

    def main_stream(self): 
        trail_time = self.TT
        LP_t0 = 0
        while True:
            self.up_time = self.renewal_time + clock() - self.downtime

            try:
                l = self.stream_q.get(block=False)
            except Empty:
                continue
            
            _id = l[0]

            self.price_array[self.MARKET_epics[_id]] = l[1]
            self.bid_array[self.MARKET_epics[_id]] = l[2]
            self.time_array.append(round(clock(), 2))

            # update price trails accordingly:
            t_loop = round(clock(), 2)
            self.TaT = self.up_time - self.time_array[-len(self.trail_array[self.MARKET_epics[0]])]
            if self.TaT == trail_time:
                for epic in self.MARKET_epics:
                    self.trail_array[epic] = np.append(self.trail_array[epic], self.price_array[epic])
                    self.trail_array[epic] = np.delete(self.trail_array[epic], 0)
            elif self.TaT > trail_time:
                del_array = []
                for n in range(len(self.trail_array['CS.D.GBPUSD.CFD.IP']), 0, -1):
                    if self.up_time - self.time_array[-n] >= trail_time:
                        del_array.append(n)
                    else:
                        break
                for epic in self.MARKET_epics:
                    self.trail_array[epic] = np.append(self.trail_array[epic], self.price_array[epic])
                    self.trail_array[epic] = np.delete(self.trail_array[epic], del_array)
                del self.time_array[0:-len(self.trail_array[self.MARKET_epics[0]])]
            else:
                for epic in self.MARKET_epics:
                    self.trail_array[epic] = np.append(self.trail_array[epic], self.price_array[epic])

            # Stat Arb Prelims:
            if self.up_time >= trail_time:
                try:
                    self.live_pairs = self.live_q.get(block=False)
                except Empty:
                    pass

                if self.live_pairs != []:
                    y = self.price_array[self.live_pairs[0]]
                    x = self.price_array[self.live_pairs[1]]
                    if y > x:
                        e_t = y - (self.m * x) - self.c
                    else:
                        e_t = (y - (self.m * x) - self.c) * -1
                    try:
                        self.calc_q.put({'epic0': self.live_pairs[0],
                                         'epic1': self.live_pairs[1],
                                         'epic0_ofr': y,
                                         'epic1_ofr': x,
                                         'epic0_bid': self.bid_array[self.live_pairs[0]],
                                         'epic1_bid': self.bid_array[self.live_pairs[1]],
                                         'epic0_ave': self.y_bar,
                                         'epic1_ave': self.x_bar,
                                         'trig': self.trigger,
                                         'e_ave': self.e_ave,
                                         'e_t': e_t},
                                         block=False)
                    except Full:
                        pass

            self.stream_q.task_done()

    def epic_stream(self, EPIC, epic_id):
        global client_ID
        global LS_addr
        global XST
        global CST

        bid = 0.0
        ofr = 0.0
        updated = False
        updates = 0
        t0 = clock()

        # Connect:
        session_details = {}
        cmd = ''
        while True:
            try:
                server_msg = urlopen(self.LS_server_name + self.connection_path, self.connection_parameters)
                cmd = server_msg.readline().decode().rstrip()
                break
            except Exception:
                print('Connection Error when connecting to LS server. Waiting 1...')
                sleep(1)
        if cmd == "OK":
            while True:
                new_line = server_msg.readline().decode().rstrip()
                if new_line:
                    detail_key, detail_value = new_line.split(":",1)
                    session_details[detail_key] = detail_value
                else:
                    break
            SessionId = session_details['SessionId']
            ControlAddress = "https://" + session_details['ControlAddress']
            SessionTime = int(session_details['KeepaliveMillis']) / 100
            cmd = ''

        # Subscribe:
        self.local_subscription(session_id=SessionId, control_addr=ControlAddress, table_no=epic_id, sub="MARKET", epic=EPIC, field_schema="OFFER BID")

        # Stream:
        while True:
            try:
                pkt = server_msg.readline().decode().rstrip()
            except Exception:
                pkt = 'none'

            try:
                pkt[0]
            except IndexError:
                print('pkt =', pkt)
                continue
    
            if pkt[0].isdigit():
                l = pkt.split('|')
                if l[1]:
                    if l[1][0].isdigit():
                        ofr = float(l[1])
                        updated = True
                if l[2]:
                    if l[2][0].isdigit():
                        bid = float(l[2])
                        updated = True
                if updated:
                    self.spr_array[EPIC] = (ofr - bid) / (0.01 if "JPY" in EPIC else 0.0001)
                    self.stream_q.put([epic_id, ofr, bid])
                    self.stream_q.join()
                updated = False

            else:
                self.LS_server_name = LS_addr
                self.connection_parameters = bytes(urlencode({"LS_op2": "create",
                                                              "LS_cid": "mgQkwtwdysogQz2BJ4Ji kOj2Bg",
                                                              "LS_adapter_set": "DEFAULT",
                                                              "LS_user": client_ID,
                                                              "LS_password": "CST-" + CST + "|XST-" + XST,
                                                              "LS_keepalive_millis": self.keepalive,
                                                              "LS_content_length": self.data_buffer
                                                              }), 'utf-8')
                # Stream Maintenance:
                if pkt == 'none':
                    print("Error receiving updates from the server.")

                    # try to establish a connection unless session time expires
                    while True:
                        try:
                            urlopen('http://www.google.com') # a reliable site that will likely always respond
                            connected = True
                            break
                        except Exception:
                            connected = False

                    # re-connect and subscribe:
                    try:
                        server_msg = urlopen(self.LS_server_name + self.connection_path, self.connection_parameters)
                        cmd = server_msg.readline().decode().rstrip()
                    except Exception:
                        continue
                    if cmd == "OK":
                        while True:
                            new_line = server_msg.readline().decode().rstrip()
                            if new_line:
                                detail_key, detail_value = new_line.split(":",1)
                                session_details[detail_key] = detail_value
                            else:
                                break
                        SessionId = session_details['SessionId']
                        ControlAddress = "https://" + session_details['ControlAddress']
                        SessionTime = int(session_details['KeepaliveMillis']) / 100
                        cmd = ''
                    self.local_subscription(session_id=SessionId, control_addr=ControlAddress, table_no=id, sub="MARKET", epic=EPIC, field_schema="OFFER BID")

                # Continue receiving if a probe message is received:
                elif pkt == "PROBE":
                    z = 1
                    continue

                # Rebind the session if a loop command is received:
                elif pkt == "LOOP":
                    # re-connect and subscribe:
                    try:
                        server_msg = urlopen(self.LS_server_name + self.connection_path, self.connection_parameters)
                        cmd = server_msg.readline().decode().rstrip()
                        break
                    except Exception:
                        continue
                    if cmd == "OK":
                        while True:
                            new_line = server_msg.readline().decode().rstrip()
                            if new_line:
                                detail_key, detail_value = new_line.split(":",1)
                                session_details[detail_key] = detail_value
                            else:
                                break
                        SessionId = session_details['SessionId']
                        ControlAddress = "https://" + session_details['ControlAddress']
                        SessionTime = int(session_details['KeepaliveMillis']) / 100
                        cmd = ''
                    self.local_subscription(session_id=SessionId, control_addr=ControlAddress, table_no=id, sub="MARKET", epic=EPIC, field_schema="OFFER BID")

                # Stop receiving and then make-safe session if sync error (bad Session ID) is received: 
                elif pkt == "SYNC ERROR" or pkt == "ERROR" or pkt == "END":
                    print("Error encountered. Starting from scratch...\n")
                    # re-connect and subscribe:
                    try:
                        server_msg = urlopen(self.LS_server_name + self.connection_path, self.connection_parameters)
                        cmd = server_msg.readline().decode().rstrip()
                        break
                    except Exception:
                        continue
                    if cmd == "OK":
                        while True:
                            new_line = server_msg.readline().decode().rstrip()
                            if new_line:
                                detail_key, detail_value = new_line.split(":",1)
                                session_details[detail_key] = detail_value
                            else:
                                break
                        SessionId = session_details['SessionId']
                        ControlAddress = "https://" + session_details['ControlAddress']
                        SessionTime = int(session_details['KeepaliveMillis']) / 100
                        cmd = ''
                    self.local_subscription(session_id=SessionId, control_addr=ControlAddress, table_no=id, sub="MARKET", epic=EPIC, field_schema="OFFER BID")

    def start_stream(self):
        #Initiate a dedicated thread to receive live data:
        self.stream_thread = Thread(target=self.main_stream, daemon=True)
        self.coint_thread  = Thread(target=self.cointegration, daemon=True)
        self.stream_thread.start()
        self.coint_thread.start()
        i = 0
        for epic in self.MARKET_epics:
            self.epic_stream_thread = Thread(target=self.epic_stream, args=(epic, i), daemon=True)
            self.epic_stream_thread.start()
            i += 1
    
    def subscribe(self, sub="", epic="", field_schema="", buffer="0", mode="MERGE", frequency="0"):
        start_time = clock()

        if self.subscription_count < len(self.MARKET_epics):
            self.subscription_count += 1

        subscription_parameters = {"LS_session": self.SessionId,
                                   "LS_Table": str(self.subscription_count),
                                   "LS_op": "add",
                                   "LS_id": sub + ":" + epic,
                                   "LS_schema": field_schema,
                                   "LS_mode": mode,
                                   "LS_requested_buffer_size": buffer,
                                   "LS_requested_max_frequency": frequency,
                                   }

        for n in range(0,20):
            sub_time = start_time - clock()
            if sub_time >= self.SessionTime:
                break
            try:
                s = post(self.ControlAddress + self.control_path, data=subscription_parameters)
                if s.status_code != 200 or 'error' in s.text.lower():
                    info_logger.error('Subscription error - %d %s', s.status_code, s.text)
                    print("Subscription error:", s.status_code, s.text)
                break
            except RequestException:
                error_logger.error('Connection Error - Subscription.')
                sleep(30)

    def local_subscription(self, session_id="", control_addr="", table_no="", sub="", epic="", field_schema="", mode="MERGE"):

        subscription_parameters = {"LS_session": session_id,
                                   "LS_Table": table_no,
                                   "LS_op": "add",
                                   "LS_id": sub + ":" + epic,
                                   "LS_schema": field_schema,
                                   "LS_mode": mode,
                                   "LS_requested_buffer_size": "0",
                                   "LS_requested_max_frequency": "1",
                                   }

        for n in range(0,20):
            try:
                s = post(control_addr + self.control_path, data=subscription_parameters)
                if s.status_code != 200 or 'error' in s.text.lower():
                    info_logger.error('Subscription error - %d %s', s.status_code, s.text)
                    print("Subscription error:", s.status_code, s.text)
                break
            except RequestException:
                error_logger.error('Connection Error - Subscription.')
                sleep(6)

    def bind(self):
        bind_parameters = bytes(urlencode({"LS_session": self.SessionId
                           }), 'utf-8')
        #Bug out and log info if this loop fails to re-bind the session.
        for n in range(0,20):
            try:
                urlopen(self.ControlAddress + self.binding_path, bind_parameters)
                break
            except RequestException:
                error_logger.error('Connection Error - Bind.')
                sleep(30)
                continue

    def unsubscribe_all(self):
        for n in range(0, self.subscription_count + 1):
            self.subscription_count += -1
            unsubscription_parameters = {"LS_session": self.SessionId,
                                         "LS_Table": n,
                                         "LS_op": "delete"
                                         }
            for n in range(0,20):
                try:
                    unsub = post(self.ControlAddress + self.control_path, data=unsubscription_parameters)
                    break
                except RequestException:
                    sleep(30)
            if unsub.status_code != 200 or "error" in unsub.text.lower():
                print("Error encountered when unsubscribing.")
            else:
                print('unsub', unsub.status_code)

    def terminate(self):
        destruction_parameters = {"LS_session": self.SessionId,
                              "LS_op": "destroy",
                              }
        try:
            end_session = post(self.ControlAddress + self.control_path, data=destruction_parameters)
        except RequestException:
            pass
        return end_session.status_code, end_session.text

    def rebind_session(self):
        self.bind()
        self.connect()
        self.subscription_count = -1
        for epic in self.MARKET_epics:
            self.subscribe(sub="MARKET", epic=epic, field_schema="OFFER BID")

    def make_safe(self):
        #(A full unload followed by a full reload):
        self.unsubscribe_all()
        self.terminate()
        self.connect()
        self.subscription_count = -1
        for epic in MARKET_epics:
            self.subscribe(sub="MARKET", epic=epic, field_schema="OFFER BID")

    def combo_grid(self, MARKET_epics):
        combos = []
        for epic1 in MARKET_epics:
            for epic2 in MARKET_epics:
                if epic1 == epic2:
                    continue
                else:
                    combo = [epic1, epic2]
                    if combo not in combos and combo[::-1] not in combos:
                        combos.append(combo)
        return combos

    def cointegration(self):
        global in_limbo
        LP_t0 = 0
        while True:
            #print('TT:', self.TT, 'TaT:', round(self.TaT, 0), 'TA:', len(self.trail_array["CS.D.GBPUSD.CFD.IP"]), 'LPs:', self.live_pairs, end='\r')

            if self.live_pairs == [] and self.up_time >= self.TT:
                coint_t0 = clock()
                for c in self.combinations:
                    try:
                        if self.spr_array[c[0]] > self.max_spr or self.spr_array[c[1]] > self.max_spr:
                            continue
                    except KeyError:
                        pass
                        continue
                    y = self.trail_array[c[0]]
                    x = self.trail_array[c[1]]
                    if y.size > x.size:
                        y = np.delete(y, [n for n in range(0, (y.size - x.size))])
                        pass
                    elif x.size > y.size:
                        x = np.delete(x, [n for n in range(0, (x.size - y.size))])
                        pass
                    if y.size < 300 or x.size < 300:
                        continue
                    y_bar = np.mean(y)
                    x_bar = np.mean(x)

                    # initial linear regression:
                    m = np.sum(x * y) / np.sum(x**2)
                    mu = y_bar - (m * x_bar)
                    if m <= 0:
                        continue

                    # residuals lagged and differenced: (get rid of the last item not the first one?)
                    Z      = y - ((m * x) - mu)
                    Z_t_1  = Z[2:]          # x1
                    dZ_t   = Z[1:] - Z[:-1] # y
                    dZ_t   = dZ_t[1:]       # y
                    dZ_t_1 = Z[2:] - Z[:-2] # x2

                    # multi-regression on residuals:
                    denom = (np.sum(Z_t_1**2) * np.sum(dZ_t_1**2)) - np.sum(Z_t_1 * dZ_t_1)**2

                    delta = ((np.sum(dZ_t_1**2) * np.sum(Z_t_1 * dZ_t)) - (np.sum(Z_t_1 * dZ_t_1) * np.sum(dZ_t_1 * dZ_t))) / denom
                    phi   = ((np.sum(Z_t_1**2) * np.sum(dZ_t_1 * dZ_t)) - (np.sum(Z_t_1 * dZ_t_1) * np.sum(Z_t_1 * dZ_t))) / denom
                    beta  = np.mean(dZ_t) - (delta * np.mean(Z_t_1)) - (phi * np.mean(dZ_t_1))

                    # cointegration test:
                    SE_delta   = sqrt(np.sum((dZ_t - (delta * Z_t_1) - (phi * dZ_t_1) - beta)**2) / (len(dZ_t) - 3))
                    t_stat = delta / SE_delta

                    if t_stat <= -3.37:
                        # record results for analysis:
                        t_stamp = str(datetime.now())[:-10].replace(":", "") + " hrs"
                        if not path.exists(r'C:\Users\Josh\Documents\Forex\Logs\e_t\\' + str(self.TT) + '\\' + 'Spreads' + '\\' + str(self.max_spr)):
                            makedirs(r'C:\Users\Josh\Documents\Forex\Logs\e_t\\' + str(self.TT) + '\\' + 'Spreads' + '\\' + str(self.max_spr))
                        with open(r'C:\Users\Josh\Documents\Forex\Logs\e_t\\' + str(self.TT) + '\\' + 'Spreads' + '\\' + str(self.max_spr) + '\\' + t_stamp + '.csv', 'w') as csv_f:
                            csv_w = writer(csv_f, lineterminator='\n')
                            for i in range(0,len(Z)):
                                csv_w.writerow([y[i], x[i], Z[i]])
                        # constants:
                        self.m       = m
                        self.c       = mu
                        self.y_bar   = y_bar
                        self.x_bar   = x_bar
                        self.trigger = STD(Z) * 2
                        self.e_ave   = np.mean(Z)
                        self.live_pairs = [c[0], c[1]]
                        #print('Pair found:', self.live_pairs[0][5:11], self.live_pairs[1][5:11])
                        LP_t0 = clock()
                        break
                    else:
                        continue
       
            elif self.live_pairs != [] and clock() - LP_t0 >= self.TT and in_limbo:
                # Re-evaluate cointegration if no changes after an entire trail time (future option - constantly re-evaluate cointegration?):
                try:
                    if self.spr_array[self.live_pairs[0]] > self.max_spr or self.spr_array[self.live_pairs[1]] > self.max_spr:
                        continue
                except KeyError:
                    pass
                    continue
                y = self.trail_array[self.live_pairs[0]]
                x = self.trail_array[self.live_pairs[1]]
                if y.size > x.size:
                    y = np.delete(y, [n for n in range(0, (y.size - x.size))])
                    pass
                elif x.size > y.size:
                    x = np.delete(x, [n for n in range(0, (x.size - y.size))])
                    pass
                if y.size < 300 or x.size < 300:
                    continue

                y_bar = np.mean(y)
                x_bar = np.mean(x)

                # initial linear regression:
                m = np.sum(x * y) / np.sum(x**2)
                mu = y_bar - (m * x_bar)
                if m <= 0:
                    self.live_pairs = []
                    continue

                # residuals lagged and differenced:
                Z      = y - ((m * x) - mu)
                Z_t_1  = Z[2:]          # x1
                dZ_t   = Z[1:] - Z[:-1] # y
                dZ_t   = dZ_t[1:]       # y
                dZ_t_1 = Z[2:] - Z[:-2] # x2

                # multi-regression on residuals:
                denom = (np.sum(Z_t_1**2) * np.sum(dZ_t_1**2)) - np.sum(Z_t_1 * dZ_t_1)**2

                delta = ((np.sum(dZ_t_1**2) * np.sum(Z_t_1 * dZ_t)) - (np.sum(Z_t_1 * dZ_t_1) * np.sum(dZ_t_1 * dZ_t))) / denom
                phi   = ((np.sum(Z_t_1**2) * np.sum(dZ_t_1 * dZ_t)) - (np.sum(Z_t_1 * dZ_t_1) * np.sum(Z_t_1 * dZ_t))) / denom
                beta  = np.mean(dZ_t) - (delta * np.mean(Z_t_1)) - (phi * np.mean(dZ_t_1))

                # cointegration test:
                SE_delta   = sqrt(np.sum((dZ_t - (delta * Z_t_1) - (phi * dZ_t_1) - beta)**2) / (len(dZ_t) - 3))
                t_stat = delta / SE_delta

                if t_stat <= -3.37:
                    # record results for analysis:
                    t_stamp = str(datetime.now())[:-10].replace(":", "") + " hrs"
                    if not path.exists(r'C:\Users\Josh\Documents\Forex\Logs\e_t\\' + str(self.TT) + '\\' + 'Spreads' + '\\' + str(self.max_spr)):
                            makedirs(r'C:\Users\Josh\Documents\Forex\Logs\e_t\\' + str(self.TT) + '\\' + 'Spreads' + '\\' + str(self.max_spr))
                    with open(r'C:\Users\Josh\Documents\Forex\Logs\e_t\\' + str(self.TT) + '\\' + 'Spreads' + '\\' + str(self.max_spr) + '\\' + t_stamp + '.csv', 'w') as csv_f:
                        csv_w = writer(csv_f, lineterminator='\n')
                        for i in range(0,len(Z)):
                            csv_w.writerow([y[i], x[i], Z[i]])
                    # constants:
                    self.m       = m
                    self.c       = mu
                    self.y_bar   = y_bar
                    self.x_bar   = x_bar
                    self.trigger = STD(Z) * 2
                    self.e_ave   = np.mean(Z)
                    LP_t0 = clock()

                else:
                    self.live_pairs = []
                    #print('LPs re-checked and set to empty', round(clock(), 3))
                    continue

            if self.live_pairs == [] and in_limbo == False:
                in_limbo = True

    def price_history(self, epic):
        hdrs = self.headers
        hdrs['VERSION'] = '3'

        time_now  = datetime.utcnow()
        time_then = time_now - datetime.timedelta(hours=(self.TT / 3600))
        time_now  = str(time_now).replace(" ", "T")[:19].replace(":", r"%3A")
        time_then = str(time_then).replace(" ", "T")[:19].replace(":", r"%3A")

        max_points = str(floor(10000 / len(self.MARKET_epics))) # Limit = 10000 data points per week 
        page_size  = max_points
        r = get(self.r00t + "/prices/" + epic + "?resolution=MINUTE&from=" + time_then + "&to=" + time_now + "&max=" + max_points + "&pageSize=" + page_size, headers=hdrs).text
        r = eval(r.replace("null", '""').replace("true", '"True"').replace("false", '"False"'))
        
        ask_a = np.array([])
        for x in r['prices']:
            ask_a = np.append(ask_a, x['closePrice']['ask'])

        return ask_a


# Rules of Engagement:
class Statistical_Arbitrage():

    MARKET_epics = [\
                "CS.D.GBPUSD.CFD.IP", "CS.D.USDJPY.CFD.IP", "CS.D.EURGBP.CFD.IP", "CS.D.EURJPY.CFD.IP", "CS.D.EURUSD.CFD.IP", "CS.D.GBPJPY.CFD.IP", \
                "CS.D.AUDJPY.CFD.IP", "CS.D.AUDUSD.CFD.IP", "CS.D.AUDCAD.CFD.IP", "CS.D.USDCAD.CFD.IP", "CS.D.NZDUSD.CFD.IP", "CS.D.NZDJPY.CFD.IP", \
                "CS.D.AUDEUR.CFD.IP", "CS.D.AUDGBP.CFD.IP", "CS.D.CADJPY.CFD.IP", "CS.D.NZDGBP.CFD.IP", "CS.D.NZDEUR.CFD.IP", "CS.D.NZDCAD.CFD.IP"]
    stop_db      = {epic: 0.0 for epic in MARKET_epics}
    pip_db       = {epic: 0.0 for epic in MARKET_epics}
    guaranteed_stop = 'true'
    assisted = False

    def __init__(self, calc_q, msg_q, status_q, live_q, log_q, plot_q, headers, creds, TT, max_spr, entry=2):
        self.r00t    = "https://demo-api.ig.com/gateway/deal"
        self.headers = headers
        self.creds   = creds

        self.calc_q   = calc_q
        self.msg_q    = msg_q
        self.status_q = status_q
        self.live_q   = live_q
        self.log_q    = log_q
        self.plot_q   = plot_q

        self.entry     = entry
        self.in_trade  = False
        self.error_log = []
        self.TT        = TT
        self.max_spr   = max_spr

        pip_stops     = []
        self.max_stop = 4
        for epic in self.MARKET_epics:
            stop_deets = self.stop_info(epic)
            self.pip_db[epic] = stop_deets[0]
            if stop_deets[1] == 'POINTS':
                self.stop_db[epic] = stop_deets[2]
                pip_stops.append(stop_deets[2])
            else:
                self.stop_db[epic] = str((stop_deets[2] / 100) / stop_deets[0])
                pip_stops.append(stop_deets[3])
        self.max_stop = min(pip_stops)
    
    def stat_arb(self):
        alert    = False
        entering = False
        above    = False
        below    = False
        global in_limbo

        t0 = clock()
        time_log = []

        while True:
            try:
                package = self.calc_q.get(block=False)
            except Empty:
                continue
            
            # code to auto-close trades if connection was lost used to be here

            if package['epic0_ofr'] > package['epic1_ofr']:
                upper_epic = package['epic0']
                lower_epic = package['epic1']

                upper_ofr  = package['epic0_ofr']
                lower_ofr  = package['epic1_ofr']

                upper_bid  = package['epic0_bid']
                lower_bid  = package['epic1_bid']

                upper_ave  = package['epic0_ave']
                lower_ave  = package['epic1_ave']
            else:
                upper_epic = package['epic1']
                lower_epic = package['epic0']

                upper_ofr  = package['epic1_ofr']
                lower_ofr  = package['epic0_ofr']

                upper_bid  = package['epic1_bid']
                lower_bid  = package['epic0_bid']

                upper_ave  = package['epic1_ave']
                lower_ave  = package['epic0_ave']

            e = package['e_t']
            centre = package['e_ave']
            threshold = package['trig']
            self.error_log.append(e)

            if e <= centre - (threshold * 2) or e >= centre + (threshold * 2):
                if self.in_trade:
                    self.close_position(close_long)
                    self.close_position(close_short)
                    if below:
                        trade_logger.info('LONG, %s, %d, %d, %f, %f' % (long_dealID, self.TT, self.max_spr, long_open, longSprOpn, upper_bid, round(upper_bid - upper_ofr, 5)))
                        trade_logger.info('SHORT, %s, %d, %d, %f, %f' % (short_dealID, self.TT, self.max_spr, short_open, shrtSprOpn, lower_ofr, round(lower_bid - lower_ofr, 5)))
                    else:
                        trade_logger.info('LONG, %s, %d, %d, %f, %f' % (long_dealID, self.TT, self.max_spr, long_open, longSprOpn, lower_bid, round(lower_bid - lower_ofr, 5)))
                        trade_logger.info('SHORT, %s, %d, %d, %f, %f' % (short_dealID, self.TT, self.max_spr, short_open, shrtSprOpn, upper_ofr, round(upper_bid - upper_ofr, 5)))
                    #self.plot_q.put([upper_epic, lower_epic, self.error_log, centre, threshold, datetime.now()])
                self.live_q.put([])
                self.error_log = []
                self.in_trade  = False
                below          = False
                above          = False
                in_limbo       = True
                continue

            if in_limbo:
                #CC_logger.info('limbo, %s, %s, %f, %f' % (upper_epic, lower_epic, e, threshold))
                if e > (centre + threshold) or e < (centre - threshold):
                    alert = True
                    in_limbo = False
                    if e < centre:
                        below = True
                    else:
                        above = True

            if alert:
                #print('Alert: %s, %s' % (upper_epic[5:11], lower_epic[5:11]), end='\r')
                if below:
                    if e >= (centre - threshold):
                       alert    = False
                       entering = True
                else:
                    if e <= (centre + threshold):
                        alert    = False
                        entering = True

            if entering:
                # 1. Setup 
                if below:
                    # Long position on upper, short position on lower.
                    upper_stop = self.stop_db[upper_epic]
                    lower_stop = self.stop_db[lower_epic]
                    if type(upper_stop) != float:
                        upper_stop = ceil(upper_ofr * float(upper_stop))
                    if type(lower_stop) != float:
                        lower_stop = ceil(lower_bid * float(lower_stop))
                    upper_limDist = ceil((upper_ave - upper_ofr) / self.pip_db[upper_epic])
                    lower_limDist = ceil((lower_bid - lower_ave) / self.pip_db[lower_epic])
                    long_open  = upper_ofr
                    short_open = lower_bid
                    shrtSprOpn = lower_bid - lower_ofr
                    longSprOpn = upper_bid - upper_ofr
         
                    long_params = {
                                "orderType": "MARKET",
                                "epic": upper_epic,
                                "direction": "BUY",
                                "size": "1",
                                "guaranteedStop": 'false',
                                "stopDistance": str(upper_stop),
                                #"limitDistance": str(upper_limDist),
                                "forceOpen": "true",
                                "expiry": "-",
                                "currencyCode": upper_epic[8:11]
                                }
                    short_params = {
                                "orderType": "MARKET",
                                "epic": lower_epic,
                                "direction": "SELL",
                                "size": "1",
                                "guaranteedStop": 'false',
                                "stopDistance": str(lower_stop),
                                #"limitDistance": str(lower_limDist),
                                "forceOpen": "true",
                                "expiry": "-",
                                "currencyCode": lower_epic[8:11]
                                }

                else:
                    # Long position on lower, short position on upper.
                    upper_stop = self.stop_db[upper_epic]
                    lower_stop = self.stop_db[lower_epic]
                    if type(upper_stop) != float:
                        upper_stop = ceil(upper_bid * float(upper_stop))
                    if type(lower_stop) != float:
                        lower_stop = ceil(lower_ofr * float(lower_stop))
                    upper_limDist = ceil((upper_bid - upper_ave) / self.pip_db[upper_epic])
                    lower_limDist = ceil((lower_ave - lower_ofr) / self.pip_db[upper_epic])
                    short_open = upper_bid
                    long_open  = lower_ofr
                    shrtSprOpn = upper_bid - upper_ofr
                    longSprOpn = lower_bid - lower_ofr
                    
                    long_params = {
                                "orderType": "MARKET",
                                "epic": lower_epic,
                                "direction": "BUY",
                                "size": "1",
                                "guaranteedStop": 'false',
                                "stopDistance": str(lower_stop),
                                #"limitDistance": str(lower_limDist),
                                "forceOpen": "true",
                                "expiry": "-",
                                "currencyCode": lower_epic[8:11]
                                }
                    short_params = {
                                "orderType": "MARKET",
                                "epic": upper_epic,
                                "direction": "SELL",
                                "size": "1",
                                "guaranteedStop": 'false',
                                "stopDistance": str(upper_stop),
                                #"limitDistance": str(upper_limDist),
                                "forceOpen": "true",
                                "expiry": "-",
                                "currencyCode": upper_epic[8:11]
                                }
                
                # 2. Open Positions
                long_dealRef  = self.create_position(long_params)
                short_dealRef = self.create_position(short_params)
                long_tkt      = self.confirmation(long_dealRef, 'open')
                short_tkt     = self.confirmation(short_dealRef, 'open')

                try:
                    long_status = long_tkt['status']
                    long_dealID = long_tkt['dealId']
                except KeyError:
                    long_status = ""
                    long_dealID = ""
                try:
                    short_status = short_tkt['status']
                    short_dealID = short_tkt['dealId']
                except KeyError:
                    short_status = ""
                    short_dealID = ""
            
                if long_status == "OPEN" or short_status == "OPEN":
                    self.in_trade = True
                    print('TRADE OPEN: %s, %s' % (upper_epic[5:11], lower_epic[5:11]))
                    close_long = {
                                  "orderType": "MARKET",
                                  "dealId": long_dealID,
                                  "direction": "SELL",
                                  "size": "1",
                                  "timeInForce": "EXECUTE_AND_ELIMINATE"}
                    close_short = {
                                   "orderType": "MARKET",
                                   "dealId": short_dealID,
                                   "direction": "BUY",
                                   "size": "1",
                                   "timeInForce": "EXECUTE_AND_ELIMINATE"}
                else:
                    self.live_q.put([])
                    in_limbo = True
                    print('Trades failed to open.')

                entering = False
                    
            if self.in_trade:
                if self.assisted:
                    while True:
                        instruction = input('In trade. Enter "next" when done: ')
                        if instruction == "next":
                            self.live_q.put([])
                            self.error_log = []
                            self.in_trade  = False
                            live_trade     = False
                            below          = False
                            in_limbo       = True
                            break
                        else:
                            continue
                    continue

                if below:
                    if e >= centre:
                        self.close_position(close_long)
                        self.close_position(close_short)
                        self.live_q.put([])
                        #self.plot_q.put([upper_epic, lower_epic, self.error_log, centre, threshold, datetime.now()])
                        self.error_log = []
                        self.in_trade  = False
                        live_trade     = False
                        below          = False
                        in_limbo       = True
                        trade_logger.info('LONG, %s, %d, %d, %f, %f' % (long_dealID, self.TT, self.max_spr, long_open, longSprOpn, upper_bid, round(upper_bid - upper_ofr, 5)))
                        trade_logger.info('SHORT, %s, %d, %d, %f, %f' % (short_dealID, self.TT, self.max_spr, short_open, shrtSprOpn, lower_ofr, round(lower_bid - lower_ofr, 5)))
                else:
                    if e <= centre:
                        self.close_position(close_long)
                        self.close_position(close_short)
                        self.live_q.put([])
                        #self.plot_q.put([upper_epic, lower_epic, self.error_log, centre, threshold, datetime.now()])
                        self.error_log = []
                        self.in_trade  = False
                        live_trade     = False
                        above          = False
                        in_limbo       = True
                        trade_logger.info('LONG, %s, %d, %d, %f, %f' % (long_dealID, self.TT, self.max_spr, long_open, longSprOpn, lower_bid, round(lower_bid - lower_ofr, 5)))
                        trade_logger.info('SHORT, %s, %d, %d, %f, %f' % (short_dealID, self.TT, self.max_spr, short_open, shrtSprOpn, upper_ofr, round(upper_bid - upper_ofr, 5)))

    def plotter(self):
        # --- MOVED TO MAIN THREAD ---
        n = 0
        while True:
            try:
                plot_data = self.plot_q.get(block=False)
            except Empty:
                continue

            std = sum(plot_data[2]) / len(plot_data[2])
            STDs_minor = np.array(plot_data[1]) - np.array(plot_data[2])
            STDs_major = np.array(plot_data[1]) + np.array(plot_data[2])

            stamp = str(datetime.now())[:-10].replace(":", "") + " hrs"
            fig = plt.figure()

            plt.title('%s vs. %s \nentry = %d' % (plot_data[3], plot_data[4], self.entry))
            axes = plt.gca()
            #axes.set_xlim([])
            axes.set_ylim([plot_data[0][0] + (5 * std), plot_data[0][0] - (5 * std)])
            plt.xlabel('Time (s)')
            plt.ylabel('Spread')
            plt.grid(True)

            plt.plot(plot_data[0])
            plt.plot(plot_data[1])
            plt.plot(STDs_minor)
            plt.plot(STDs_major)

            fig.savefig(r"C:\Users\Josh\Documents\Forex\Logs\Plots\%s" % stamp)
            plt.close('all')

            del STDs_minor
            del STDs_major

    def run(self):
        self.statarb_thread = Thread(target=self.stat_arb, daemon=True)
        self.statarb_thread.start()

    def stop_info(self, epic):
        results   = get(self.r00t + "/markets/" + epic, headers=self.headers, data=self.creds).text
        results   = eval(results.replace("true", "True").replace("false", "False").replace("null", "None"))
        pip_scale = results['instrument']['onePipMeans']
        pip_scale = float(pip_scale[:pip_scale.find(" ")])

        if self.guaranteed_stop == 'true':
            stop_units = results['dealingRules']['minControlledRiskStopDistance']['unit']
            min_stop   = results['dealingRules']['minControlledRiskStopDistance']['value']
        else:
            stop_units = results['dealingRules']['minNormalStopOrLimitDistance']['unit']
            min_stop   = results['dealingRules']['minNormalStopOrLimitDistance']['value']

        if stop_units != 'POINTS':
            pips = ceil(((min_stop / 100) / pip_scale) * float(results['snapshot']['offer']))
        else:
            pips = min_stop

        return [pip_scale, stop_units, min_stop, pips]

    def create_position(self, params={}):
        global XST
        global CST
        disconnected = False
        open_parameters = dumps(params)
        self.headers['X-SECURITY-TOKEN'] = XST
        self.headers['CST']              = CST

        try:
            r = post(self.r00t + '/positions/otc', headers=self.headers, data=open_parameters)
            open_ticket = eval(r.text)
            open_dealRef = open_ticket['dealReference']

        except RequestException as RE:
            disconnected = True
            open_dealRef = ""
            sleep(1)

        except SyntaxError:
            self.log_q.put(['position error', {'statusCode': r.status_code, 'rbody': r.text, 'epic': eval(open_parameters)['epic'], 'inst': 'open'}])
            open_dealRef = ""
            return open_dealRef

        except KeyError:
            self.log_q.put(['position error', {'statusCode': r.status_code, 'rbody': r.text, 'epic': eval(open_parameters)['epic'], 'inst': 'open'}])
            open_dealRef = ""
            return open_dealRef
        
        if disconnected:
            error_logger.debug('Connection Error - Create Position')
            pass

        return open_dealRef

    def close_position(self, params={}):
        global XST
        global CST
        disconnected = False
        close_parameters = dumps(params)

        close_headers = self.headers
        close_headers['_method'] = "DELETE"
        close_headers['X-SECURITY-TOKEN'] = XST
        close_headers['CST']              = CST

        while True:
            try:
                r = post(self.r00t + '/positions/otc', headers=close_headers, data=close_parameters)
                close_ticket = eval(r.text)
                close_dealRef = close_ticket['dealReference']
                break

            except RequestException:
                disconnected = True
                close_dealRef = ""
                while True:
                    if clock() - self.trade_start_time <= self.ave_trade_duration:
                        continue
                    else:
                        break
                    break

            except SyntaxError:
                close_dealRef = ""
                break

            except KeyError:
                close_dealRef = ""
                break

        if disconnected:
            error_logger.debug('Connection Error - Close Position')

        del self.headers['_method']

        return close_dealRef

    def confirmation(self, dealRef, type):
        try:
            r = get(self.r00t + '/confirms/' + dealRef, headers=self.headers)
            ct = r.text.replace("null", '""').replace("true", '"True"').replace("false", '"False"')
        except RequestException:
            error_logger.debug('Connection Error - no confirmation for trade %s', dealRef)
            tkt = {}
            return tkt

        try:
            tkt = eval(ct)
            tkt['inst'] = type
            tkt['statusCode'] = r.status_code
            self.log_q.put(['trade', tkt])
        except SyntaxError:
            self.log_q.put(['confirmation error', {'statusCode': r.status_code, 'rbody': r.text, 'inst': type, 'dealRef': dealRef}])
            tkt = {}
        return tkt


# House Keeping:
def command_line(plot_q):
    while True:
        instruction = input("{0:-^80}\n".format("Type 'exit' and press Enter to stop TITAN: "))
        if instruction == "exit":
            plot_q.put('exit')
        else:
            pass

def plotter(TT):
    p1 = ''
    p2 = ''
    market_close = datetime(datetime.now().year, datetime.now().month, datetime.now().day, hour=21, minute=0, second=0) + relativedelta(weekday=FR(1))
 
    while True:
        try:
            plot_data = Plot_Q.get(block=False)
        except Empty:
            continue
        if plot_data == 'exit':
            break

        UT = plot_data[3] + plot_data[4]
        LT = plot_data[3] - plot_data[4]
        UTL = np.array([UT for n in plot_data[2]])
        LTL = np.array([LT for n in plot_data[2]])

        fig = plt.figure()

        plt.title('%s vs. %s \n Trail Time = %s' % (plot_data[0], plot_data[1], str(TT)))
        plt.xlabel('Time (s)')
        plt.ylabel('Error')
        plt.grid(True)

        plt.plot(plot_data[2])
        plt.plot(UTL)
        plt.plot(LTL)

        stamp = str(datetime.now())[:-10].replace(":", "") + " hrs"
        fig.savefig(r"C:\Users\Josh\Documents\Forex\Logs\Plots\Error Term\%s" % stamp)
        plt.clf()
        #plt.pause(0.00005)
        p1 = plot_data[0]
        p2 = plot_data[1]

        if datetime.utcnow() > market_close:
            print('Markets closed. Stopping TITAN.')
            break



#---------------------------------- END OF CONSTRUCTION ----------------------------------#

#Release the T.I.T.A.N.

clock()
broker = IG_API(Message_Q, Trade_Status, Log_Q, Sy_Q)
logger = Log(Message_Q)

broker.run_mail_service()
logger.run()

#Login:
broker.login()
if broker.market_status("CS.D.GBPUSD.CFD.IP") != "TRADEABLE":
    while True:
        instruction = input('Markets closed. Type "exit" or "continue" and press enter to stop or start TITAN.')
        if instruction == exit:
            break

#Obtain security tokens:
LS_pswd = "CST-" + CST + "|XST-" + XST

#Initiate live data:
live_data = Lightstreamer(LS_addr, LS_pswd, client_ID, StatArb_Q, Live_Pairs, Message_Q, Log_Q, Sy_Q, Plot_Q, broker.headers, broker.creds)

#Initiate trading strategy: 
strategy = Statistical_Arbitrage(StatArb_Q, Message_Q, Trade_Status, Live_Pairs, Log_Q, Plot_Q, broker.headers, broker.creds, live_data.TT, live_data.max_spr)
strategy.run()

#Connect:
live_data.connect()
live_data.start_stream()

#Enable user command & control capability:
Thread(target=command_line, args=(Plot_Q,), daemon=True).start()

# Plotting:
plotter(live_data.TT)

#Unsubscribe:
live_data.unsubscribe_all()

#End session:
live_data.terminate()
broker.logout()

info_logger.info('up time: %d down time: %d = %d percent', live_data.up_time, live_data.downtime, \
                    round(((live_data.up_time - live_data.downtime) / live_data.up_time) * 100, 2))

with open('trail_array.csv', 'w') as csv_l:
    csv_w = writer(csv_l, lineterminator='\n')
    csv_w.writerow([str(datetime.utcnow()).replace("T", " "), str(live_data.TT), str(live_data.TaT)])
    for row in range(0, live_data.trail_array['CS.D.GBPUSD.CFD.IP'].size):
        csv_w.writerow([live_data.trail_array[epic][row] for epic in live_data.MARKET_epics])
print(' -- END -- ')


# -----------------------------------------  END  -------------------------------------------- #