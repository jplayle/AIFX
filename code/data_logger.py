from requests.exceptions import	RequestException
from requests import (get, put,	post, delete)
from urllib.request	import urlopen
from urllib.parse import urlencode
from csv import	(reader, writer)
from time import (clock, sleep)
from os	import (path, makedirs)
from datetime import datetime, timedelta
#from calendar import weekday
#from threading import Thread
#from getpass import	getpass
from json import dumps
from sys import	exit
#import numpy as	np

"""
NOTES etc
- updates are on the minute, every minute
- connection loss handling
- subscription loss handling 
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
	keepalive	 = "30000" #max value from server (values higher than this return this value)
	content_len  = "3600" # revise this - what values possible?
	rate_limit   = 2  #(30 non-trading requests per minute) - still applies to lightstreamer requests?
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
	max_session_time   = 6 * 3600 #6hrs, as per IG API docs
	refresh_t_minus    = 300      #5 mins before the tokens expire
	
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
		
		self.headers.pop('X-SECURITY-TOKEN', None) #clear old tokens from HTTP request headers
		self.headers.pop('CST', None)
		
		#Send the post request to log in:
		while True:
			try:
				r =	post(self.r00t + "/session", headers=self.headers, data=self.creds)
				self.login_time = datetime.utcnow()
				sleep(self.rate_limit)
				if r.status_code ==	200:
					break
			except RequestException:
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

	def logout(self):
		#NEVER CALL LOGOUT WITHOUT AN IMMEDIATE SUBSEQUENT & NON-TRHEADED CALL TO LOGIN()
		try:
			end	= delete(self.r00t + "/session", headers=self.headers)
			sleep(self.rate_limit)
			return True
		except RequestException:
			return False

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
		
		def process_stream_control():
			session_details = {}
			init_resp = read_stream()
			if init_resp == "OK":
				while True:
					new_line = read_stream()
					if new_line:
						if '|' not in new_line: # extract session details
							detail_key, detail_value =	new_line.split(":",1)
							session_details[detail_key] = detail_value
						elif '|' in new_line:
							try:
								data    = new_line.split("|")
								epic_id = int(data.pop(0).split(",")[0])
							except ValueError:
								continue
							epic = self.target_epics[epic_id]
							process_data(epic, data)
					else:
						break
				self.SessionId = session_details['SessionId']
				self.ControlAddress = "https://" + session_details['ControlAddress']
				self.SessionTime = int(session_details['KeepaliveMillis']) / 100
				return True
			else:
				return False

		def process_data(_epic, _data):
			END  = data.pop(-1)
			UTM  = data.pop(-1)
			if UTM != '':
				self.updates_t_array[_epic]['CURR'] = datetime.fromtimestamp(int(UTM) / 1000.0)
				if self.updates_t_array[_epic]['PREV'] == None: #dev: previous update time needs to be queried from the files on start-up sequence
					self.updates_t_array[_epic]['PREV'] = self.updates_t_array[_epic]['CURR'] - timedelta(minutes=1) #remove hard code of interval

			x = 0
			for d in data:
				if d not in self.void_chars:
					self.epic_data_array[_epic][self.targ_fields[x]] = d
				x += 1
				
			return END
			
		def connect():
			while True:
				try:
					self.server_conn = urlopen(self.LS_addr + self.connection_path, bytes(urlencode(self.connection_parameters), 'utf-8')) # open connection to server
					process_stream_control()
					break
				except Exception:
					sleep(self.rate_limit)

		def subscribe_all():
			for table_no, epic in enumerate(self.target_epics):
				sub_params = self.subscription_params
				sub_params.update({"LS_session": self.SessionId,
									"LS_Table":  str(table_no),
									"LS_id":     ":".join([self.sub, epic, self.interval])})
				try: 
					s =	post(self.ControlAddress + self.control_path, data=sub_params)
					if s.status_code !=	200	or 'error' in s.text.lower():
						# do something to manage dropped subscriptions
						continue
				except RequestException:
					# same as above comment
					continue
					
			return True
		
		def bind():
			#this method seems to be really slow - resub could be faster but riskier
			self.bind_session_params['LS_session'] = self.SessionId
			try:
				self.server_conn = urlopen(self.ControlAddress + self.binding_path, bytes(urlencode(self.bind_session_params), 'utf-8'))
				process_stream_control()
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
				epic_id = int(data.pop(0).split(",")[0])
			except ValueError:
				# STREAM MAINTENANCE
				if pkt == 'PROBE':
					continue
				elif pkt == 'LOOP':
					bind()
					continue
				elif 'END' in pkt:
					print('END', pkt)
					#log error/end reason
					sleep(3) #LS docs state not recommended to attempt re-connect 'immediately' - exact time unspecified)
					connect()
					subscrible_all()
					continue
				else:
					continue
			except ConnectionError as e:
				print(e)
				self.logout()
				self.login()
				connect()
				subscribe_all()
				continue
			
			epic     = self.target_epics[epic_id]
			CONS_END = process_data(epic, data)
			
			if CONS_END == "1": #end of candle
				if epic_id == 0:
					print(self.updates_t_array[epic]['CURR'], self.epic_data_array[epic])
				t_curr = self.updates_t_array[epic]['CURR']
				t_prev = self.updates_t_array[epic]['PREV']
				t_diff = int((t_curr - t_prev).seconds / 60)
				if t_diff > 1:
					for m in range(1, t_diff):
						gap_time = t_prev + timedelta(minutes=m)
						#write blank row for each missing minute
				# WRITE CURRENT OHLCV DATA
				self.epic_data_array[epic] = {field: '' for field in self.targ_fields}  #reset interval data
				self.updates_t_array[epic]['PREV'] = t_curr
				
				if (datetime.utcnow() - self.login_time).seconds >= self.max_session_time - self.refresh_t_minus:
					print('refresh cycle')
					#obtain new security tokens et al
					self.logout()
					self.login()
					connect()
					subscribe_all()

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

	#command_line()

	broker.logout()
	
	
if __name__	== '__main__':
	main()
