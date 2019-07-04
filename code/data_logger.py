
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
        
        self.stream_q = Queue()
        # Data streams:
        self.subscription_count = -1

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
               
                epic_id = int(pkt[:pkt.find(",")])

                #update the EPIC's price when a new value has arrived:
                l = pkt.split('|')
                
                if l[2] != '' and l[2] != '$' and l[2] != '#':
                    self.bid_array[self.MARKET_epics[epic_id]] = float(l[2])
                if l[1] != '' and l[1] != '$' and l[1] != '#':
                    self.price_array[self.MARKET_epics[epic_id]] = float(l[1])
                    self.time_array.append(round(clock(),2))
                else:
                    continue

                #update price trails accordingly:
                
                
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


def command_line(plot_q):
    while True:
        instruction = input("{0:-^80}\n".format("Type 'exit' and press Enter to stop TITAN: "))
        if instruction == "exit":
            plot_q.put('exit')
        else:
            pass



#---------------------------------- END OF CONSTRUCTION ----------------------------------#

clock()
broker = IG_API(Message_Q, Trade_Status, Log_Q, Sy_Q)

#Login:
broker.login()

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

#Unsubscribe:
live_data.unsubscribe_all()

#End session:
live_data.terminate()
broker.logout()



# -----------------------------------------  END  -------------------------------------------- #