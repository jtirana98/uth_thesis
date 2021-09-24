'''
Registry program: Provides information about the available edge points of 
the system.
'''
import threading
import Pyro4
from lxml import etree
import time
import string
import os.path
from os import path
from collections import deque
import yaml
import math
import re

class bcolors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKCYAN = '\033[96m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'

Pyro4.config.SERIALIZER = "json"
PYRO_SERIALIZERS_ACCEPTED="serpent /usr/bin/python3 -Wignore -m Pyro4.naming"
host_name = "192.168.2.102"
port_updateReg = 9557
#port_getAccess = 9558
timeout = 15 #period for each zone to update its values

sessions = {} #zoneID:timestamp
lock_sessions = threading.Lock()

registries = {} #zoneID:regInfo
lock_registries = threading.Lock()


@Pyro4.expose
class RegistryManager():
	'''
	EdgeServer --> (N:1) Registry
	Edge Server periodically sends to Registry its information 
	(id, ip/port, nodes - sevices) and 	update 	its session. 
	'''
	def __init__(self):
		pass

	def registry(self, zoneID, info):
		lock_sessions.acquire()
		print(f"{bcolors.WARNING}UpdateReg: New registry update from zone %s{bcolors.ENDC}" %(zoneID))
		session_start = time.time()
		
		#update session
		
		sessions.update({zoneID:session_start})
		lock_sessions.release()

		#update reg info
		lock_registries.acquire()
		registries.update({zoneID:info})
		lock_registries.release()
	
	def get(self, zone):
		print(f"{bcolors.OKBLUE}AccessReg: sending info for zone:%d{bcolors.ENDC}"%zone);
		lock_registries.acquire()
		if zone in registries:
			return_val =  registries.get(zone)
		else:
			return_val = None
		lock_registries.release()

		return return_val

	def getAll(self):
		print(f"{bcolors.OKBLUE}AccessReg: sending info for all zones{bcolors.ENDC}");
		return_val = ""
		lock_registries.acquire()
		for reg in registries.keys():
			return_val = return_val + "-"+ reg + " " + registries.get(reg) + "\n"
		lock_registries.release()
		return(return_val)
		

class GarbageRegCollector():
	def __init__(self):
		print(f"{bcolors.OKGREEN}Garbage Registries Collector Started{bcolors.ENDC}")

	def collect(self):
		'''
		checks if a session has been expired
		'''
		while True:
			time.sleep(timeout + (timeout/2)- 2)
			lock_sessions.acquire()
			time_now = time.time()
			lock_registries.acquire()
			zones_sessions = sessions.keys()
			todelete = []
			for zone in zones_sessions:
				time_session = sessions.get(zone)
				if(time_now - time_session > timeout):
					print(f"{bcolors.OKGREEN}GarbageRegCollector: The session for zone:%s expired, zone is deleted{bcolors.ENDC}" %zone);
					todelete.append(zone)
			for z in todelete:
				sessions.pop(z)
				registries.pop(z)
			lock_registries.release()
			lock_sessions.release()


def main():
	#initialize all threads		
	regdeamon = Pyro4.Daemon(host=host_name ,port=port_updateReg)
	reg_object = RegistryManager()
	uri = regdeamon.register(reg_object,objectId='REGISTRYMANAGER')
	srv_th = threading.Thread(target=regdeamon.requestLoop)
	srv_th.daemon=True
	srv_th.start()

	print(f"{bcolors.WARNING}Registry Service Started{bcolors.ENDC}");
	#print(f"{bcolors.OKBLUE}Access Registries Service Started{bcolors.ENDC}");

	garbageCollector = GarbageRegCollector()
	garbageCollector.collect()


if __name__ == '__main__':
	main()