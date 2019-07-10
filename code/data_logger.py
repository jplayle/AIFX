
# Nerve	centre
from dateutil.relativedelta	import (relativedelta, FR)
from queue import (Queue, LifoQueue, Empty,	Full)
from requests.exceptions import	RequestException
from requests import (get, put,	post, delete)
from collections import	OrderedDict
from urllib.request	import urlopen
from urllib.parse import urlencode
from urrlib.error import URLError
from csv import	(reader, writer)
import matplotlib.pyplot as	plt
from time import (clock, sleep)
from os	import (path, makedirs)
from datetime import datetime, timedelta
from math import (sqrt,	ceil)
from calendar import weekday
from threading import Thread
from getpass import	getpass
from json import dumps
from sys import	exit
import numpy as	np

"""
FINDINGS
- updates are on the minute, every minute
"""


class IG_API():
	
	target_epics =	["CS.D.GBPUSD.CFD.IP", "CS.D.USDJPY.CFD.IP", "CS.D.EURGBP.CFD.IP", "CS.D.EURJPY.CFD.IP", "CS.D.EURUSD.CFD.IP", "CS.D.GBPJPY.CFD.IP",	\
					 "CS.D.AUDJPY.CFD.IP", "CS.D.AUDUSD.CFD.IP", "CS.D.AUDCAD.CFD.IP", "CS.D.USDCAD.CFD.IP", "CS.D.NZDUSD.CFD.IP", "CS.D.NZDJPY.CFD.IP",	\
					 "CS.D.AUDEUR.CFD.IP", "CS.D.AUDGBP.CFD.IP", "CS.D.CADJPY.CFD.IP", "CS.D.NZDGBP.CFD.IP", "CS.D.NZDEUR.CFD.IP", "CS.D.NZDCAD.CFD.IP"]
	
	sub          = "CHART"
	mode         = "MERGE"
	interval     = "1MINUTE"
	targ_fields  = ["BID_OPEN", "BID_HIGH", "BID_LOW", "BID_CLOSE", "LTV"]
	aux_fields   = ["UTM", "CONS_END"]
	field_schema = " ".join(targ_fields + aux_fields)
	buffer       = "0"
	max_freq     = "0"
	keepalive	 = str(60 * 5 * 1000) #(interval * multiplication factor * convert to milliseconds)
	content_len  = "360000" # revise this to 
	rate_limit   = 2  #(30 non-trading requests per minute)
	void_chars   = ['', '$', '#']
	
	subscription_params = {"LS_op": "add",
						   "LS_schema": field_schema,
						   "LS_mode":   mode,
						   "LS_requested_buffer_size":   buffer,
						   "LS_requested_max_frequency": max_freq}
	bind_session_params = {'LS_content_length':    content_len,
							'LS_keepalive_millis': keepalive,
							'LS_session': ''}
	subscription_count = 0
	SessionId          = ''
	ControlAddress     = ''
	SessionTime        = ''
	
	connection_path = "/lightstreamer/create_session.txt"
	binding_path	= "/lightstreamer/bind_session.txt"
	control_path	= "/lightstreamer/control.txt"
	
	epic_data_array = {}
	for epic in target_epics:
		epic_data_array[epic] = {field: '' for field in targ_fields}
	updates_t_array = {epic: {'PREV': None, 'CURR': None} for epic in target_epics} #Last Update Time - query from start-up sequence in later versions

	def __init__(self, live=False):
		self.XST = ''
		self.CST = ''
		self.client_ID = ''
		self.LS_addr = ''
		self.LS_pswd = ''
		
		self.r00t = "https://demo-api.ig.com/gateway/deal"
		self.IG_API_key = "a0a64071668c6d0b81f8d0f6e839d94046630645"
		self.username = "AIFX_data"
		self.password = "Edge540p1enxt"
			
		self.headers = {
			'Content-Type': 'application/json; charset=UTF-8',
			'Accept': 'application/json;	charset=UTF-8',
			'VERSION': '1',
			'X-IG-API-KEY': self.IG_API_key
			}
		self.creds = dumps({
			'identifier': self.username,
			'password':   self.password
			})
		
		self.connection_parameters = {"LS_op2": "create",
									  "LS_cid": "mgQkwtwdysogQz2BJ4Ji kOj2Bg",
									  "LS_adapter_set": "DEFAULT",
									  "LS_keepalive_millis": self.keepalive,
									  "LS_content_length":   self.content_len}
				
		self.subscription_count = 0

	def login(self):
		# login to IG demo API and retrieve security tokens, session ID, session server details etc

		#Send the post request to log in:
		while True:
			try:
				r =	post(self.r00t + "/session", headers=self.headers, data=self.creds)
				sleep(self.rate_limit)
				if r.status_code ==	200:
					break
			except RequestException:
				sleep(self.rate_limit)
				continue

		#Obtain security tokens & client ID:
		self.CST       = str(r.headers['CST'])
		self.XST       = str(r.headers['X-SECURITY-TOKEN'])
		self.client_ID = str(r.text[r.text.find("clientId")+11:r.text.find("clientId")+20])
		self.LS_pswd   = "CST-" + self.CST + "|XST-" + self.XST

		#Update request authentication details:
		self.headers.update({'X-SECURITY-TOKEN': self.XST, 'CST': self.CST})
		self.connection_parameters.update({"LS_user": self.client_ID, "LS_password": self.LS_pswd})

		#Obtain the URL for the Lighstreamer server: (potentially a more efficient/robust way to extract this exists)
		txt = r.text
		s0 = txt.find('lightstreamerEndpoint',0)
		s1 = txt.find(':',s0)	+ 2
		s2 = txt.find('"',s1)
		self.LS_addr =	txt[s1:s2]
		# get's the status of a market e.g. 'TRADEABLE' and returns the result
		results = get(self.r00t +	"/markets/"	+ epic,	headers=self.headers, data=self.creds).text
		results = eval(results.replace("true", "True").replace("false", "False").replace("null", "None"))
		market_state = results['snapshot']['marketStatus']
		return market_state

	def logout(self):
		for n	in range(0,20):
			try:
				end	= delete(self.r00t + "/session", headers=self.headers)
				if end.status_code != 200 or 'error' in	end.text.lower():
					print('Error logging out of broker.')
					print(end.text)
				else:
					print('Logged out of broker successfully.')
				break
			except RequestException:
				sleep(30)
				continue

	def startup_sequence(self):
		"""
		1. Check if data files exist and retrieve previous update time from the last row if they do
		2. Write necessary number of blank rows based on difference between previous time from step 1 and the current time - use datetime.utcnow() for current time
		3. For each epic data file: set self.updates_t_array[epic]['PREV'] to the last written time from step 2
		- Because of step 3, the writer algorithm will fill in any blank rows that are required between finishing the start-up sequence and writing the first data
		"""		
		return None
				
	def data_stream(self):
		
		def read_stream():
			return self.server_conn.readline().decode().rstrip()

		def connect():
			session_details = {} # info for session management and control
			init_resp =	'' # initial response from server about connection status
			while	True:
				try:
					self.server_conn = urlopen(self.LS_addr + self.connection_path, bytes(urlencode(self.connection_parameters), 'utf-8')) # open connection to server
					init_resp        = read_stream() # get initial response
					break
				except Exception:
					print('Connection Error	when connecting	to LS server. Waiting 1...')
					sleep(self.rate_limit)
			if init_resp == "OK":
				while True:
					new_line = read_stream()
					if new_line: # extract session details
						detail_key, detail_value =	new_line.split(":",1)
						session_details[detail_key] = detail_value
					else:
						break
				self.SessionId = session_details['SessionId']
				self.ControlAddress = "https://" + session_details['ControlAddress']
				self.SessionTime = int(session_details['KeepaliveMillis']) / 100
				init_resp = ''

		def subscribe_all():
			for epic in self.target_epics:
				sub_params = self.subscription_params
				sub_params.update({"LS_session": self.SessionId,
									"LS_Table":  str(self.subscription_count),
									"LS_id":     ":".join([self.sub, epic, self.interval])})
				try: 
					s =	post(self.ControlAddress + self.control_path, data=sub_params)
					if s.status_code !=	200	or 'error' in s.text.lower():
						return False
				except RequestException:
					return False
				self.subscription_count += 1
					
			return True
		
		def bind():
			self.bind_session_params['LS_session'] = self.SessionId
			try:
				s =	post(self.ControlAddress + self.binding_path, data=self.bind_session_params)
				print('bind response', s.text)
				if s.status_code !=	200	or 'error' in s.text.lower():
						return False
			except RequestException:
				return False
			return True
			
		connect()
		sub_status = subscribe_all()

		#	Stream:
		while True:
			try:
				pkt	 = read_stream()
				data = pkt.split("|")
			except ValueError:
				if pkt == 'PROBE':
					continue
				elif pkt == 'LOOP':
					bind()
					continue
				elif pkt[:3] == 'END':
					#log error/end reason
					sleep(3) #LS docs state not recommended to attempt re-connect 'immediately' - exact time unspecified)
					connect()
					subscrible_all()
					continue
			except ConnectionError:
				connect()
				resub = subscrible_all()
				if not resub:
					continue
				
			epic_id  = int(data.pop(0).split(",")[0])
			epic     = self.target_epics[epic_id]
			CONS_END = data.pop(-1)
			UTM      = data.pop(-1)
			if UTM != '':
				self.updates_t_array[epic]['CURR'] = datetime.fromtimestamp(int(UTM) / 1000.0)
				if self.updates_t_array[epic]['PREV'] == None: #dev: previous update time needs to be queried from the files on start-up sequence
					self.updates_t_array[epic]['PREV'] = self.updates_t_array[epic]['CURR'] - timedelta(minutes=1) #remove hard code of interval

			x = 0
			for d in data:
				if d not in self.void_chars:
					self.epic_data_array[epic][self.targ_fields[x]] = d
				x += 1
			
			if CONS_END == "1": #end of candle
				t_prev = self.updates_t_array[epic]['PREV']
				t_diff = (self.updates_t_array[epic]['CURR'] - t_prev).seconds / 60
				if t_diff > 1:
					for m in range(1, t_diff):
						gap_time = t_prev + timedelta(minutes=m)
						#write blank row for each missing minute
				# WRITE CURRENT OHLCV DATA
				self.epic_data_array[self.target_epics[epic_id]] = {field: '' for field in self.targ_fields}  #reset interval data
				self.updates_t_array[epic]['PREV'] = self.updates_t_array[epic]['CURR']
				continue


		#(A full unload followed by a	full reload):
		self.unsubscribe_all()
		self.terminate()
		self.connect()
		self.subscription_count =	-1
		for epic in MARKET_epics:
			self.subscribe(sub="MARKET",	epic=epic, field_schema="OFFER BID")

	def price_history(self, epic):
		hdrs = self.headers
		hdrs['VERSION'] =	'3'

		time_now	= datetime.utcnow()
		time_then	= time_now - datetime.timedelta(hours=(self.TT / 3600))
		time_now	= str(time_now).replace(" ",	"T")[:19].replace(":", r"%3A")
		time_then	= str(time_then).replace(" ", "T")[:19].replace(":", r"%3A")

		max_points = str(floor(10000 / len(self.MARKET_epics))) #	Limit =	10000 data points per week 
		page_size  = max_points
		r = get(self.r00t	+ "/prices/" + epic	+ "?resolution=MINUTE&from=" + time_then + "&to=" +	time_now + "&max=" + max_points	+ "&pageSize=" + page_size,	headers=hdrs).text
		r = eval(r.replace("null", '""').replace("true", '"True"').replace("false", '"False"'))
		
		ask_a	= np.array([])
		for x	in r['prices']:
			ask_a = np.append(ask_a, x['closePrice']['ask'])

		return ask_a

	def current_price(self, epic):
		results =	get(self.r00t +	"/markets/"	+ epic,	headers=self.headers, data=self.creds).text
		results =	eval(results.replace("true", "True").replace("false", "False").replace("null", "None"))
		price	= float(results['snapshot']['offer'])
		bid =	float(results['snapshot']['bid'])
		return [price, bid]

	def patch_data(self):
		"""
		- Details tbc.
		"""
		return None
		
def	command_line():
	while True:
		instruction =	input("{0:-^80}\n".format("'exit' to stop data logger."))
		if instruction ==	"exit":
			exit()
		else:
			pass



def	main():
	
	broker = IG_API()

	broker.login()

	broker.data_stream()

	command_line()

	broker.unsubscribe_all()

	broker.terminate()
	broker.logout()
	
	
if __name__	== '__main__':
	main()