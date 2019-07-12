from requests.exceptions import	RequestException
from requests import (get, put,	post, delete)
from urllib.request	import urlopen
from urllib.parse import urlencode
from csv import	(reader, writer)
from time import (clock, sleep, time)
from os	import (path, makedirs)
import pytz
from datetime import datetime, timedelta
from datetime import time as dt_time
#from calendar import weekday
#from threading import Thread
#from getpass import	getpass
from json import dumps
from sys import	exit
from socket import timeout as socket_timeout_exception
#import numpy as	np

"""
NOTES etc
- updates are on the minute, every minute
DEV
- what to do about $ and # - ignore or use to identify a missing price?
"""


class IG_API():
	
	target_epics =	["CS.D.GBPUSD.CFD.IP", "CS.D.USDJPY.CFD.IP", "CS.D.EURGBP.CFD.IP", "CS.D.EURJPY.CFD.IP", "CS.D.EURUSD.CFD.IP", "CS.D.GBPJPY.CFD.IP",	\
					 "CS.D.AUDJPY.CFD.IP", "CS.D.AUDUSD.CFD.IP", "CS.D.AUDCAD.CFD.IP", "CS.D.USDCAD.CFD.IP", "CS.D.NZDUSD.CFD.IP", "CS.D.NZDJPY.CFD.IP",	\
					 "CS.D.AUDEUR.CFD.IP", "CS.D.AUDGBP.CFD.IP", "CS.D.CADJPY.CFD.IP", "CS.D.NZDGBP.CFD.IP", "CS.D.NZDEUR.CFD.IP", "CS.D.NZDCAD.CFD.IP"]
	
	sub          = "CHART"
	mode         = "MERGE"
	interval     = "1MINUTE"
	interval_val = 1 #integer value of interval, expressed in minutes
	targ_fields  = ["BID_OPEN", "BID_HIGH", "BID_LOW", "BID_CLOSE", "LTV"]
	aux_fields   = ["UTM", "CONS_END"]
	field_schema = " ".join(targ_fields + aux_fields)
	buffer       = "0"
	max_freq     = "0"
	keepalive	 = "30000" #max value from server (values higher than this return this value)
	content_len  = "3600" # revise this - what values possible?
	rate_limit   = 2  #(30 non-trading requests per minute) - still applies to lightstreamer requests?
	null_chars   = ['$', '#'] #real empty string values ('' implies no change since previous value)
	void_chars   = ['', '$', '#'] #in these cases make no changes to data
	
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
	connection_timeout = int(int(keepalive) * 0.9 / 1000) #connection loss - server connection must timeout to be reset if nothing received after this time (allow 10% head room for good measure)
	max_session_time   = 6 * 3600 #6hrs, as per IG API docs - new security tokens will be obtained after this time (logout, login again)
	refresh_t_minus    = max_session_time * 0.01 #refresh when session time reaches 99% of maximum
	connection_path    = "/lightstreamer/create_session.txt"
	binding_path	   = "/lightstreamer/bind_session.txt"
	control_path	   = "/lightstreamer/control.txt"
	
	epic_data_array = {}
	prev_data_array = {}
	for epic in target_epics:
		epic_data_array[epic] = {field: '' for field in targ_fields}
		prev_data_array[epic] = {field: '' for field in targ_fields}
	updates_t_array           = {epic: {'PREV': None, 'CURR': None} for epic in target_epics} #Last Update Time - query from start-up sequence in later versions
	
	FX_market_global_open_t  = dt_time(22) #open hour MUST be in GMT/UTC as a stationary reference (doesn't change for DST etc) 
	FX_market_global_close_t = dt_time(21) #close hour MUST be in GMT/UTC as a stationary reference (doesn't change for DST etc)
	local_tz                 = pytz.timezone("Europe/London") #set timezone string to be the same as the broker account - data timestamps are then handled accordingly

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

	def logout(self):
		#NEVER CALL LOGOUT WITHOUT AN IMMEDIATE SUBSEQUENT & NON-TRHEADED CALL TO LOGIN()
		try:
			end	= delete(self.r00t + "/session", headers=self.headers)
			sleep(self.rate_limit)
			return True
		except RequestException:
			return False
		
	def handle_tgap(self, dt0, dt1):
		"""
		- return missing datetimes at self.interval separation between two datetime objects, excluding market closures
		- just an initial brute force iterative method - faster method possible by doing time diffs (although on testing this method proves more than adequate)
		- speed: fri-sat takes < 0.1s, 1 week takes ~1s (i7 processor, ubuntu 16)
		- doesn't check for public holidays/other misc. market closures
		"""
		def utc_delta(local_dt):
			"""
			- returns number of hours difference between a given datetime+timezone and utc
			- required because data timestamps are in 'account local time' which may be not be same as utc due to different timezone, DST etc
			"""
			try:
				utc_dt = self.local_tz.localize(local_dt, is_dst=None).astimezone(pytz.utc) #get n hrs between utc and timezone local time
			except pytz.exceptions.AmbiguousTimeError:
				utc_dt = self.local_tz.localize(local_dt, is_dst=False).astimezone(pytz.utc) #clocks go back = same time occurs twice hence ambiguous error = dst is ending
			except pytz.exceptions.NonExistentTimeError:
				utc_dt = self.local_tz.localize(local_dt, is_dst=True).astimezone(pytz.utc) #clocks go fwd = entire hour skipped hence non-existent error = dst is starting
			return int((local_dt - utc_dt.replace(tzinfo=None)).seconds / 3600)
		
		n_mins = int((dt1 - dt0).total_seconds() / (60 * self.interval_val))
		missing_datetimes = []
		
		for m in range(1, n_mins):
			dt0  += timedelta(minutes=1) 
			utc_t = dt0 - timedelta(hours=utc_delta(dt0)) #timestamp from server shifted to utc for comparison to market hours which are in utc
			w_day = utc_t.weekday()
			
			if w_day not in [4, 5, 6]: #not friday, saturday or sunday
				missing_datetimes.append(dt0)
				
			elif w_day == 4: #friday - check market closure
				iday_time = dt_time(utc_t.hour, utc_t.minute) #intra-day time, shifted to utc
				if iday_time < self.FX_market_global_close_t:
					missing_datetimes.append(dt0)
					
			elif w_day == 6: #sunday - check market closure
				iday_time = dt_time(utc_t.hour, utc_t.minute) #intra-day time, shifted to utc
				if iday_time > self.FX_market_global_open_t:
					missing_datetimes.append(dt0)
					
		return missing_datetimes

	def startup_sequence(self):
		"""
		1. Check if data files exist and retrieve previous update time from the last row if they do
		2. Write necessary number of blank rows based on difference between previous time from step 1 and the current time - use datetime.utcnow() for current time
		3. For each epic data file: set self.updates_t_array[epic]['PREV'] to the last written time from step 2
		- Because of step 3, the writer algorithm will fill in any blank rows that are required between finishing the start-up sequence and writing the first data
		"""		
		return None
				
	def data_stream(self):
		
		def connect():
			while True:
				try:
					self.server_conn = urlopen(self.LS_addr + self.connection_path, bytes(urlencode(self.connection_parameters), 'utf-8'), timeout=self.connection_timeout) # open connection to server
					process_stream_control()
					break
				except Exception:
					sy_token_handler()
					sleep(self.rate_limit)
		
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

		def subscribe_all():
			while True: #don't let data streaming start without a full subscription
				success = False
				t0 = clock()
				while (clock() - t0) < self.connection_timeout: #only attempt subscription if connection still alive
					for table_no, epic in enumerate(self.target_epics):
						sub_params = self.subscription_params
						sub_params.update({"LS_session": self.SessionId,
											"LS_Table":  str(table_no),
											"LS_id":     ":".join([self.sub, epic, self.interval])})
						try: 
							s =	post(self.ControlAddress + self.control_path, data=sub_params)
							sleep(0.1)
							if s.status_code ==	200:
								success = True
							else:
								success = False #success might get set to true and then needs subsequent setting to false is a later sub fails
						except RequestException:
							success = False
							continue
					if success:
						break
					else:
						new_tokens = sy_token_handler() #check for security token renewal due to potentially infinite loop
						if new_tokens:
							connect()
							continue
				if success:
					break
				else:
					connect()
				
		def process_data(_epic, _data):
			IS_END = data.pop(-1)
			UTM    = data.pop(-1)
			if UTM not in self.void_chars:
				self.updates_t_array[_epic]['CURR'] = datetime.fromtimestamp(int(UTM) / 1000.0)
				if self.updates_t_array[_epic]['PREV'] == None: #dev: previous update time needs to be queried from the files on start-up sequence
					self.updates_t_array[_epic]['PREV'] = self.updates_t_array[_epic]['CURR'] - timedelta(minutes=self.interval_val)

			x = 0
			for d in data:
				if d not in self.void_chars:
					self.epic_data_array[_epic][self.targ_fields[x]] = d
				x += 1
				
			return IS_END
		
		def bind():
			self.bind_session_params['LS_session'] = self.SessionId
			try:
				self.server_conn = urlopen(self.ControlAddress + self.binding_path, bytes(urlencode(self.bind_session_params), 'utf-8'), timeout=self.connection_timeout)
				process_stream_control()
			except Exception:
				return False
			return True
			
		def on_loop_reset(current_time):
			self.prev_data_array[epic] = self.epic_data_array[epic]                 #store previous data array
			self.epic_data_array[epic] = {field: '' for field in self.targ_fields}  #reset interval data
			self.updates_t_array[epic]['PREV'] = current_time                       #store previous update time
			
		def reset_stream():
			connect()
			subscribe_all()
			
		def sy_token_handler():
			# check for if session security tokens need updating and update if so
			if (datetime.utcnow() - self.login_time).seconds >= self.max_session_time - self.refresh_t_minus:
				self.logout()
				self.login()
				return True
			else:
				return False
			
		reset_stream()

		# Stream:
		while True:
			try:
				pkt	 = read_stream()
				data = pkt.split("|")
				epic_id = int(data.pop(0).split(",")[0])
			except ValueError:
				#Stream Maintenance
				if pkt == 'PROBE':
					continue
				elif pkt == 'LOOP':
					bind()
					continue
				elif 'END' in pkt:
					print('END', pkt)
					#log error/end reason
					sleep(3) #LS docs state not recommended to attempt re-connect 'immediately' - exact time unspecified
					reset_stream()
					continue
				else:
					print('err', pkt)
					reset_stream()
			except socket_timeout_exception:
				reset_stream()
				continue
			except ConnectionError:
				reset_stream()
				continue
			
			epic     = self.target_epics[epic_id]
			CONS_END = process_data(epic, data)
			
			if CONS_END == "1": #end of candle - write data				
				t_curr = self.updates_t_array[epic]['CURR']
				t_prev = self.updates_t_array[epic]['PREV']
				t_diff = int((t_curr - t_prev).seconds / (60 * self.interval_val))
				
				if t_diff == 1:
					#use previous values if 
					for k, v in self.epic_data_array[epic].items():
						if v == '':
							self.epic_data_array[epic][k] = self.prev_data_array[epic][k] 
							
				elif t_diff > self.interval_val:
					handle_tgap(t_prev, t_curr)
					
				else:
					#log error
					self.epic_data_array[epic] = {field: '' for field in self.targ_fields}
					continue #don't write in case of server sending erroneous messages that are in the past
				
				if epic_id == 0:
					print(self.updates_t_array[epic]['CURR'], self.epic_data_array[epic]) #debug
				# WRITE CURRENT OHLCV DATA
				
				on_loop_reset(t_curr)
				
				# check for session refresh
				new_tokens = sy_token_handler()
				if new_tokens:
					reset_stream()

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
	
	dt_0 = datetime(2019, 7, 12, 20, 31, 0)
	dt_1 = datetime(2019, 7, 14, 23, 11, 0)
	t0 = clock()
	r = broker.handle_tgap(dt_0, dt_1)
	t1 = clock()
	print(r)
	print(t1 - t0)
	return
	broker.login()

	broker.data_stream()
	
	#send notification here
	#command_line()

	broker.logout()
	
	
if __name__	== '__main__':
	main()