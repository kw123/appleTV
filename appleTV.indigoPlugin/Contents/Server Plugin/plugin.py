#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# apple tv  Plugin
# Developed by Karl Wachs
# karlwachs@me.com
#pyatv is maintained by postlund
#see: https://github.com/postlund/pyatv
import datetime
import simplejson as json
import subprocess
import fcntl
import os
import sys
import pwd
import time
import Queue
import socket
import getNumber as GT
import threading
import logging
import copy
import json

from checkIndigoPluginName import checkIndigoPluginName 




dataVersion = 0.1

## Static parameters, not changed in pgm
_debugAreas					= [u"GetData",u"ReceiveData",u"Consumption",u"Basic",u"all",u"Special"]
################################################################################
# noinspection PyUnresolvedReferences,PySimplifyBooleanCheck,PySimplifyBooleanCheck
class Plugin(indigo.PluginBase):
	####-----------------			  ---------
	def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
		indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)

		#pfmt = logging.Formatter('%(asctime)s.%(msecs)03d\t%(levelname)-12s\t%(name)s.%(funcName)-25s %(msg)s', datefmt='%Y-%m-%d %H:%M:%S')
		#self.plugin_file_handler.setFormatter(pfmt)

		self.pluginShortName 			= u"appleTV"


		self.quitNow					= ""
		self.updateConnectParams		= time.time() - 100
		self.getInstallFolderPath		= indigo.server.getInstallFolderPath()+"/"
		self.indigoPath					= indigo.server.getInstallFolderPath()+"/"
		self.indigoRootPath 			= indigo.server.getInstallFolderPath().split("Indigo")[0]
		self.pathToPlugin 				= self.completePath(os.getcwd())

		major, minor, release 			= map(int, indigo.server.version.split("."))
		self.indigoRelease				= release
		self.indigoVersion 				= float(major)+float(minor)/10.



		self.pluginVersion				= pluginVersion
		self.pluginId					= pluginId
		self.pluginName					= pluginId.split(".")[-1]
		self.myPID						= os.getpid()
		self.pluginState				= u"init"

		self.myPID 						= os.getpid()
		self.MACuserName				= pwd.getpwuid(os.getuid())[0]

		self.MAChome					= os.path.expanduser(u"~")
		self.userIndigoDir				= self.MAChome + "/indigo/"
		self.indigoPreferencesPluginDir = self.getInstallFolderPath+"Preferences/Plugins/"+self.pluginId+"/"
		self.indigoPluginDirOld			= self.userIndigoDir + self.pluginShortName+"/"
		self.PluginLogFile				= indigo.server.getLogsFolderPath(pluginId=self.pluginId) +"/plugin.log"

		formats=	{   logging.THREADDEBUG: "%(asctime)s %(msg)s",
						logging.DEBUG:       "%(asctime)s %(msg)s",
						logging.INFO:        "%(asctime)s %(msg)s",
						logging.WARNING:     "%(asctime)s %(msg)s",
						logging.ERROR:       "%(asctime)s.%(msecs)03d\t%(levelname)-12s\t%(name)s.%(funcName)-25s %(msg)s",
						logging.CRITICAL:    "%(asctime)s.%(msecs)03d\t%(levelname)-12s\t%(name)s.%(funcName)-25s %(msg)s" }

		date_Format = { logging.THREADDEBUG: "%d %H:%M:%S",
						logging.DEBUG:       "%d %H:%M:%S",
						logging.INFO:        "%d %H:%M:%S",
						logging.WARNING:     "%d %H:%M:%S",
						logging.ERROR:       "%Y-%m-%d %H:%M:%S",
						logging.CRITICAL:    "%Y-%m-%d %H:%M:%S" }
		formatter = LevelFormatter(fmt="%(msg)s", datefmt="%Y-%m-%d %H:%M:%S", level_fmts=formats, level_date=date_Format)

		self.plugin_file_handler.setFormatter(formatter)
		self.indiLOG = logging.getLogger("Plugin")  
		self.indiLOG.setLevel(logging.THREADDEBUG)

		self.indigo_log_handler.setLevel(logging.INFO)
		indigo.server.log(u"initializing  ... ")

		indigo.server.log(  u"path To files:          =================")
		indigo.server.log(  u"indigo                  {}".format(self.indigoRootPath))
		indigo.server.log(  u"installFolder           {}".format(self.indigoPath))
		indigo.server.log(  u"plugin.py               {}".format(self.pathToPlugin))
		indigo.server.log(  u"Plugin params           {}".format(self.indigoPreferencesPluginDir))

		self.indiLOG.log( 0,u"logger  enabled for     0 ==> TEST ONLY ")
		self.indiLOG.log( 5,u"logger  enabled for     THREADDEBUG    ==> TEST ONLY ")
		self.indiLOG.log(10,u"logger  enabled for     DEBUG          ==> TEST ONLY ")
		self.indiLOG.log(20,u"logger  enabled for     INFO           ==> TEST ONLY ")
		self.indiLOG.log(30,u"logger  enabled for     WARNING        ==> TEST ONLY ")
		self.indiLOG.log(40,u"logger  enabled for     ERROR          ==> TEST ONLY ")
		self.indiLOG.log(50,u"logger  enabled for     CRITICAL       ==> TEST ONLY ")
		indigo.server.log(  u"check                   {}  <<<<    for detailed logging".format(self.PluginLogFile))
		indigo.server.log(  u"Plugin short Name       {}".format(self.pluginShortName))
		indigo.server.log(  u"my PID                  {}".format(self.myPID))	 
		indigo.server.log(  u"set params for indigo V {}".format(self.indigoVersion))	 


		
####

	####-----------------			  ---------
	def __del__(self):
		indigo.PluginBase.__del__(self)

	###########################		INIT	## START ########################

	####----------------- @ startup set global parameters, create directories etc ---------
	def startup(self):
		if not checkIndigoPluginName(self, indigo): 
			exit() 


		self.pythonPath					= u"/usr/bin/python2.6"
		if os.path.isfile(u"/usr/bin/python2.7"):
			self.pythonPath				= u"/usr/bin/python2.7"

		self.pluginState == "init"


		self.debugLevel = []
		for d in _debugAreas:
			if self.pluginPrefs.get(u"debug"+d, False): self.debugLevel.append(d)


		self.logFile		 	= ""
		self.logFileActive	 	= self.pluginPrefs.get(u"logFileActive2", u"standard")
		self.maxLogFileSize	 	= 1*1024*1024
		self.lastCheckLogfile	= time.time()
		self.updateStates		= {}
		self.everyxSecGetPlaying 	= float(self.pluginPrefs.get("everyxSecGetPlaying",20))
		self.everyxSecGetNewDevices	= float(self.pluginPrefs.get("everyxSecGetNewDevices",300))
		self.pathToPython3 			= self.pluginPrefs.get("pathToPython3", "/usr/local/bin/python3")
		self.indiLOG.log(20,  u"path To python3                {}".format(self.pathToPython3))
		self.indiLOG.log(20,  u"check for new devices every    {:.0f} secs".format(self.everyxSecGetNewDevices))
		self.indiLOG.log(20,  u"check for now plying  every    {:.0f} secs".format(self.everyxSecGetPlaying))


		return 


	####-----------------	 ---------
	def isValidIP(self, ip0):
		ipx = ip0.split(u".")
		if len(ipx) != 4:								return False

		else:
			for ip in ipx:
				try:
					if int(ip) < 0 or  int(ip) > 255: 	return False
				except:
														return False
		return True

	####-----------------	 ---------
	def fixIP(self, ip): # make last number always 3 digits for sorting
		if len(ip) < 7: return ip
		ipx = ip.split(u"/")[0].split(u".")
		ipx[3] = "%03d" % (int(ipx[3]))
		return u".".join(ipx)


	####-----------------	 ---------
	def isValidMAC(self, mac):
		xxx = mac.split(u":")
		if len(xxx) != 6:			return False
		else:
			for xx in xxx:
				if len(xx) != 2: 	return False
				try: 	int(xx, 16)
				except: 			return False
		return True

	####-----------------	 ---------
	def completePath(self,inPath):
		if len(inPath) == 0: return ""
		if inPath == " ":	 return ""
		if inPath[-1] !="/": inPath +="/"
		return inPath
####-------------------------------------------------------------------------####


	####-----------------  update state lists ---------
	def deviceStartComm(self, dev):
		if self.decideMyLog(u"Basic"): self.indiLOG.log(10,u"starting device:  {}  {}  {}".format(dev.name, dev.id), dev.states[u"MAC"])

		if	self.pluginState == "init":
			dev.stateListOrDisplayStateIdChanged()

		return


	####-----------------	 ---------
	def deviceStopComm(self, dev):
		if	self.pluginState != u"stop":
			if self.decideMyLog(u"Basic"): self.indiLOG.log(10,u"stopping device:  {}  {}".format(dev.name, dev.id) )
		return 

	####-----------------	 ---------
	def validatePrefsConfigUi(self, valuesDict):

		try:

			##
			self.debugLevel = []
			for d in _debugAreas:
				if valuesDict[u"debug"+d]: self.debugLevel.append(d)

			self.everyxSecGetPlaying 	= float(valuesDict["everyxSecGetPlaying"])
			self.everyxSecGetNewDevices	= float(valuesDict["everyxSecGetNewDevices"])
			self.pathToPython3			= valuesDict["pathToPython3"]
			self.indiLOG.log(20,  u"check for new devices every     {:.0f} secs".format(self.everyxSecGetNewDevices))
			self.indiLOG.log(20,  u"check for now plying  every     {:.0f} secs".format(self.everyxSecGetPlaying))
			self.indiLOG.log(20,  u"path To python3                 {}".format(self.everyxSecGetPlaying))


			return True, valuesDict
		except	Exception, e:
			if unicode(e).find(u"None") == -1:
				self.indiLOG.log(40,u"in Line {} has error={}".format(sys.exc_traceback.tb_lineno, e) )
			return (False, valuesDict, valuesDict)


	####-----------------	 ---------
	def validateDeviceConfigUi(self, valuesDict, typeId, devId):
		try:
			self.indiLOG.log(10,u"in valuesDict:{}; typeId:{}; devId:{}".format(valuesDict, typeId, devId) )
			dev = indigo.devices[devId]
			self.updateStates = {devId:{}}
			if valuesDict["overwritePIN"] != dev.states["pin"]:
				self.updateStates[devId]["pin"] = valuesDict["overwritePIN"]
			if valuesDict["overwriteIP"] != dev.states["ip"]:
				self.updateStates[devId]["ip"] = valuesDict["overwriteIP"]
			return True, valuesDict
		except	Exception, e:
			if unicode(e).find(u"None") == -1:
				self.indiLOG.log(40,u"in Line {} has error={}".format(sys.exc_traceback.tb_lineno, e) )
			return (False, valuesDict, valuesDict)

	####-----------------	 ---------
	def printConfigMenu(self,  valuesDict=None, typeId=""):
		return 

	####-----------------	 ---------
	def getNewDevicesCALLBACK(self,  valuesDict=None, typeId=""):
		self.lastGetNewDevices = 0
		return 


	###########################	   MAIN LOOP  ############################
	####-----------------init  main loop ---------
	def fixBeforeRunConcurrentThread(self):

		return True



####-----------------   main loop          ---------
	def runConcurrentThread(self):
		### self.indiLOG.log(50,u"CLASS: Plugin")


		if not self.fixBeforeRunConcurrentThread():
			self.indiLOG.log(40,u"..error in startup")
			self.sleep(10)
			return


		self.pluginState   = "running"
		self.dorunConcurrentThread()

		self. postLoop()
		self.sleep(1)
		if self.quitNow !="":
			indigo.server.log( u"runConcurrentThread stopping plugin due to:  ::::: {} :::::".format(self.quitNow))
			serverPlugin = indigo.server.getPlugin(self.pluginId)
			serverPlugin.restart(waitUntilDone=False)
		return


####-----------------   main loop            ---------
	def dorunConcurrentThread(self):

		self.indiLOG.log(20,u" start   runConcurrentThread, initialized loop settings")


		indigo.server.savePluginPrefs()
		self.pluginStartTime 	= time.time()

		self.lastGetPlaying 	= 0
		self.lastGetNewDevices	= 0
		self.loopCount 			= 0

		try:
			while True:
				self.loopCount +=1
				self.indiLOG.log(10,u"in loop #{}".format(self.loopCount))
				self.getNewDevices()
				self.getPlaying()
	
				for ii in range(10):
					self.updateChangedStatesInDeviceEdit()
					self.sleep(1)


		except	Exception, e:
			if unicode(e).find(u"None") == -1:
				self.indiLOG.log(40,u"in Line {} has error={}".format(sys.exc_traceback.tb_lineno, e))

		self.postLoop()


	###########################	   exec the loop  ############################
	####-----------------	 ---------
	def updateChangedStatesInDeviceEdit(self):
		try:
			if self.updateStates != {}:
				for devId in self.updateStates:
					if self.updateStates[int(devId)] != {}:
						dev = indigo.devices[devId]
						for state in self.updateStates[int(devId)]:
							dev.updateStateOnServer(state, self.updateStates[devId][state] )
				self.updateStates  = {}

		except	Exception, e:
			if unicode(e).find(u"None") == -1:
				self.indiLOG.log(40,u"in Line {} has error={}".format(sys.exc_traceback.tb_lineno, e))
		return 

	####-----------------	 ---------
	def getNewDevices(self):

		try:
			if time.time() - self.lastGetNewDevices < self.everyxSecGetNewDevices: return

			self.lastGetNewDevices = time.time()
		
			data = self.getscriptScan()

			if self.decideMyLog(u"Consumption"): self.indiLOG.log(10,u"=========+++++ combined:{}".format(json.dumps(data, sort_keys=True, indent=2)))

			for ip in data:
				ipFound = False
				for dev in indigo.devices.iter(u"props.isAppleTV"):
					if u"ip" not in dev.states: continue
					if dev.states[u"ip"] == ip:
						ipFound = True
						break
				if not ipFound:
					data2 = self.getatvremoteScan()
					if ip in data2:
						if self.decideMyLog(u"Consumption"): self.indiLOG.log(10,u"=========+++++ getatvremoteScan:{}".format(data2))
						data[ip][u"MAC"] 				= data2[ip][u"MAC"]
						data[ip][u"MRPCredentials"] 	= data2[ip][u"MRPCredentials"]
						data[ip][u"AIRPLAYCredentials"] = data2[ip][u"AIRPLAYCredentials"]
						data[ip][u"model"] 				= data2[ip][u"model"]

					devProps = {}
					devProps[u"isAppleTV"]					= True
					devProps[u"SupportsOnState"]			= False
					devProps[u"SupportsSensorValue"]		= False
					devProps[u"SupportsStatusRequest"]		= False
					devProps[u"AllowOnStateChange"]			= False
					devProps[u"AllowSensorValueChange"]		= False
					devProps[u"overwriteIP"]				= ip
					devProps[u"overwritePIN"]				= 1234
					devProps[u"displayS"]					= u"currentlyPlaying_Title"
					dev = indigo.device.create(
					protocol =		 indigo.kProtocol.Plugin,
					address =		 ip,
					name =			 "appletv_" + ip,
					description =	 data[ip][u"name"],
					pluginId =		 self.pluginId,
					deviceTypeId =	 "appleTV",
					props =			 devProps)
					#folder =		 self.folderNameIDSystemID,
					dev.updateStateOnServer(u"ip",ip)
				chList =[]
				for xx in [u"currentlyPlaying_MediaType",u"currentlyPlaying_DeviceState",u"currentlyPlaying_Title",  u"currentlyPlaying_Artist", 
							u"currentlyPlaying_Album",   u"currentlyPlaying_Position",   u"currentlyPlaying_Repeat", u"currentlyPlaying_Shuffle",
							u"deepSleep", u"name", u"MAC", u"model", u"identifier",
							u"MRPPort", u"MRPCredentials", u"AIRPLAYPort", u"AIRPLAYCredentials",
							u"currentlyPlaying_TotalTime"
							]:
					if self.checkIfChanged(xx, dev.states, data[ip]): chList.append({u"key":xx, u"value":data[ip][xx]}) 
				for ch in chList:
					if self.decideMyLog(u"Consumption"): self.indiLOG.log(10,u"in ch {} ".format(ch))

				dev.updateStatesOnServer(chList)

		except	Exception, e:
			if unicode(e).find(u"None") == -1:
				self.indiLOG.log(40,u"in Line {} has error={}".format(sys.exc_traceback.tb_lineno, e))

	####-----------------	 ---------
	def getPlaying(self):
		try: 
			if time.time() - self.lastGetPlaying < self.everyxSecGetPlaying: return
			self.lastGetPlaying = time.time()

			for dev in indigo.devices.iter(u"props.isAppleTV"):
				ip = dev.states[u"ip"]
				identifier = dev.states[u"identifier"]
				data = self.getscriptPlaying(identifier)
				if self.decideMyLog(u"Consumption"): self.indiLOG.log(10,u"=========+++++ combined:{}".format(json.dumps(data, sort_keys=True, indent=2)))

				chList =[]
				for xx in [u"currentlyPlaying_MediaType",u"currentlyPlaying_DeviceState",u"currentlyPlaying_Title",  u"currentlyPlaying_Artist", 
							u"currentlyPlaying_Album",   u"currentlyPlaying_Position",   u"currentlyPlaying_Repeat", u"currentlyPlaying_Shuffle",
							u"deepSleep", u"name", u"MAC", u"model", u"identifier",
							u"MRPPort", u"MRPCredentials", u"AIRPLAYPort", u"AIRPLAYCredentials",
							u"currentlyPlaying_TotalTime"
							]:
					if self.checkIfChanged(xx, dev.states, data): chList.append({u"key":xx, u"value":data[xx]}) 
				for ch in chList:
					if self.decideMyLog(u"Consumption"): self.indiLOG.log(10,u"in ch {} ".format(ch))

				# set status 
				if "result" in data and data["result"] == "failure":
						chList.append({u"key":u"status", u"value":"failure", u"uiValue":u"failure"}) 
						dev.updateStateImageOnServer(indigo.kStateImageSel.SensorTripped)
				elif "currentlyPlaying_DeviceState" in data and data[u"currentlyPlaying_DeviceState"] == u"idle":
						dev.updateStateImageOnServer(indigo.kStateImageSel.PowerOff)
						chList.append({u"key":u"status", u"value":data[u"currentlyPlaying_DeviceState"], u"uiValue":data[u"currentlyPlaying_DeviceState"]}) 
				elif "currentlyPlaying_DeviceState" in data:
						dev.updateStateImageOnServer(indigo.kStateImageSel.PowerOn)
						chList.append({u"key":u"status", u"value":data["currentlyPlaying_DeviceState"], u"uiValue":data[u"currentlyPlaying_DeviceState"]}) 

				dev.updateStatesOnServer(chList)

		except	Exception, e:
			if unicode(e).find(u"None") == -1:
				self.indiLOG.log(40,u"in Line {} has error={}".format(sys.exc_traceback.tb_lineno, e))
		return 


	####-----------------	 ---------
	def checkIfChanged(self, state, Current, New):
		try:
			if state not in New or  state not in Current: return False
			if New[state] is None: return False
			#self.indiLOG.log(10,u" state:{}, ==:{}  {} -- {}".format(state, New[state] == Current[state], New[state], Current[state]))
			if New[state] != Current[state]: return True
		except	Exception, e:
			if unicode(e).find(u"None") == -1:
				self.indiLOG.log(40,u"in Line {} has error={}".format(sys.exc_traceback.tb_lineno, e))
		return False



	####-----------------	 ---------
	def getscriptScan(self):
		"""
python3 atvscript.py scan 
{"result": "success", "datetime": "2021-03-25T21:47:46.966942-05:00", 
"devices": [
{"name": "Bedroom", "address": "192.168.1.48", "identifier": "01F74624-B8BB-4EF9-9E9E-4A6C42EEC75F", 
  "services": [{"protocol": "mrp", "port": 49153}, {"protocol": "AIRPLAY", "port": 7000}]}, 
{"name": "Living Room", "address": "192.168.1.47", "identifier": "0721B1F4-4CE5-4EA7-86B7-BE4F2FCAAA30", 
  "services": [{"protocol": "mrp", "port": 49152}, {"protocol": "AIRPLAY", "port": 7000}]}]}
		"""
		try:
			retDict = {}
			cmd = [self.pathToPython3,self.pathToPlugin+"atvscript.py","scan"]
			if self.decideMyLog(u"GetData"): self.indiLOG.log(10,u"=========getscriptScan cmd:{}".format(cmd))
			out = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
			if self.decideMyLog(u"ReceiveData"): self.indiLOG.log(10,u"=========getscriptScan out:{}".format(out))
			if len(out[0]) < 5:					return retDict
			data = json.loads(out[0])
			if self.decideMyLog(u"ReceiveData"): self.indiLOG.log(10,u"=========getscriptScan out:{}".format(out[0]))
			if u"result" not  in data:			return retDict
			if data[u"result"] != u"success": 	return retDict
		
			if u"devices" in data: 
				for device in data[u"devices"]:
					if u"address" 		in device: 
						ip = device[u"address"]
						retDict[ip]			= {}
						if u"name" 			in device: retDict[ip][u"name"] 		= device[u"name"]
						if u"identifier"	in device: retDict[ip][u"identifier"] 	= device[u"identifier"]
						if u"services" in device:
							for service in device[u"services"]:
								if u"protocol" 	in service: 
									protocol = service[u"protocol"].upper()
									if u"port" 	in service: 
										retDict[ip][protocol+u"Port"] = service[u"port"]
			if self.decideMyLog(u"ReceiveData"): self.indiLOG.log(10,u"=========+++++ retDict:{}".format(json.dumps(retDict, sort_keys=True, indent=2)))
			return retDict
		except	Exception, e:
			if unicode(e).find(u"None") == -1:
				self.indiLOG.log(40,u"in Line {} has error={}".format(sys.exc_traceback.tb_lineno, e))
				if self.decideMyLog(u"ReceiveData"): self.indiLOG.log(10,u"=========getscriptScan out[1]:{}".format(out[1]))
		return {}

	####-----------------	 ---------
	def getatvremoteScan(self):
		"""
python3 atvremote.py scan
Scan Results
========================================
       Name: Living Room
   Model/SW: 4K tvOS 14.3
    Address: 192.168.1.47
        MAC: D0:D2:B0:88:7B:77   <=========
 Deep Sleep: False
Identifiers:
 - 0721B1F4-4CE5-4EA7-86B7-BE4F2FCAAA30
 - D0:D2:B0:88:7B:77
Services:
 - Protocol: MRP, Port: 49152, Credentials: None
 - Protocol: AIRPLAY, Port: 7000, Credentials: None

       Name: Bedroom
   Model/SW: 4K tvOS 14.5
    Address: 192.168.1.48
        MAC: 40:CB:C0:D0:FF:C4
 Deep Sleep: False
Identifiers:
 - 01F74624-B8BB-4EF9-9E9E-4A6C42EEC75F
 - 40:CB:C0:D0:FF:C4
Services:
 - Protocol: MRP, Port: 49153, Credentials: None
 - Protocol: AIRPLAY, Port: 7000, Credentials: None
		"""
		try:
			retDict = {}
			cmd = [self.pathToPython3,self.pathToPlugin+"atvremote.py","scan"]
			if self.decideMyLog(u"GetData"): self.indiLOG.log(10,u"=========getatvremoteScan cmd:{}".format(cmd))
			out = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
			if self.decideMyLog(u"ReceiveData"): self.indiLOG.log(10,u"=========+++++ getatvremoteScan\n{}".format(out[0]))
			if out[0].find(u"Scan Results") 	== -1: return {}
			if out[0].find(u"       Name: ") 	== -1: return {}
			data = out[0].split(u"       Name: ")[1:]
			
			for section in data:
				ip		= section.split(u"Address: ")[1].split("\n")[0].strip()
				retDict[ip] 				= {}
				theItems 					= section.split("\n")
				retDict[ip]["name"] 		= theItems[0]
				retDict[ip][u"model"] 		= section.split(u"Model/SW: ")[1].split("\n")[0].strip()
				retDict[ip][u"MAC"] 		= section.split(u"MAC: ")[1].split("\n")[0].strip()
				retDict[ip][u"deepSleep"] 	= section.split(u"Deep Sleep: ")[1].split("\n")[0].strip()

				rest = section.split(u"Identifiers:\n")[1]
				rest = rest.split(u"\nServices:\n")
				xxx  = rest[0].split(u"\n")
				for yy in xxx:
					if yy.find(u" - ") >-1:
						zz = yy.split(" - ")[1]
						if zz.find("-")>-1: retDict[ip][u"identifier"] = zz

				xxx  = rest[1].split(u"\n")
				for yy in xxx:
					if yy.find(u"Protocol: ") >-1:
						zz = yy.split(u"Protocol: ")[1]
						gg = zz.split(", ")
						tag = gg[0].upper()
						for hh in gg[1:]:
							jj =  hh.split(u": ")
							retDict[ip][tag+jj[0]] = jj[1] 
						
			if self.decideMyLog(u"ReceiveData"): self.indiLOG.log(10,u"=========getatvremoteScan:{}".format(json.dumps(retDict, sort_keys=True, indent=2)))
			
		except	Exception, e:
			if unicode(e).find(u"None") == -1:
				self.indiLOG.log(40,u"in Line {} has error={}".format(sys.exc_traceback.tb_lineno, e))
		return retDict


	####-----------------	 ---------
	def getscriptPlaying(self, id):
		"""
python3 atvscript.py -i '0721B1F4-4CE5-4EA7-86B7-BE4F2FCAAA30' playing
{"result": "success", "datetime": "2021-03-26T12:06:31.555020-05:00", "hash": "D94143CC-6E1A-4DF6-99BB-9193B32C1BFD", 
"media_type": "unknown", 
"device_state": "playing", 
"title": "CNN Newsroom With Brianna Keilar", 
"artist": "CNN", 
"album": null, 
"genre": null, 
"total_time": 50400, 
"position": 46896, 
"shuffle": "off", 
"repeat": "off", 
"app": "YouTube TV", 
"app_id": "com.google.ios.youtubeunplugged"}		"""
		try:
			retDict = {}
			cmd = [self.pathToPython3,self.pathToPlugin+"atvscript.py","-i",id,"playing"]
			if self.decideMyLog(u"GetData"): self.indiLOG.log(10,u"=========getscriptPlaying cmd:{}".format(cmd))
			out = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
			if self.decideMyLog(u"ReceiveData"): self.indiLOG.log(10,u"=========getscriptPlaying return\n{}".format(out[0]))
			if len(out[0]) < 5:		return retDict
			data = json.loads(out[0])
			if u"result" not  in data:	return retDict
			retDict[u"result"] = data[u"result"]
			if data[u"result"] != u"success": return retDict

			if u"media_type" 	in data: retDict[u"currentlyPlaying_MediaType"] 	= data[u"media_type"]
			if u"device_state" 	in data: retDict[u"currentlyPlaying_DeviceState"]	= data[u"device_state"]
			if u"title"			in data: retDict[u"currentlyPlaying_Title"] 		= data[u"title"]
			if u"artist" 		in data: retDict[u"currentlyPlaying_Artist"] 		= data[u"artist"]
			if u"album" 		in data: retDict[u"currentlyPlaying_Album"] 		= data[u"album"]
			if u"total_time" 	in data: retDict[u"currentlyPlaying_TotalTime"] 	= data[u"total_time"]
			if u"position" 		in data: retDict[u"currentlyPlaying_Position"] 		= data[u"position"]
			if u"repeat" 		in data: retDict[u"currentlyPlaying_Repeat"] 		= data[u"repeat"]
			if u"shuffle" 		in data: retDict[u"currentlyPlaying_Shuffle"] 		= data[u"shuffle"]
			if u"app" 			in data: retDict[u"currentlyPlaying_app"] 			= data[u"app"]
			if u"app_id" 		in data: retDict[u"currentlyPlaying_appId"] 		= data[u"app_id"]
			if self.decideMyLog(u"ReceiveData"): self.indiLOG.log(10,u"=========getscriptPlaying retDict:{}".format(json.dumps(retDict, sort_keys=True, indent=2)))

		except	Exception, e:
			if unicode(e).find(u"None") == -1:
				self.indiLOG.log(40,u"in Line {} has error={}".format(sys.exc_traceback.tb_lineno, e))
				if self.decideMyLog(u"ReceiveData"): self.indiLOG.log(10,u"=========getscriptScan out[1]:{}".format(out[1]))
		return retDict



	####-----------------	 ---------
	def getauto_connect(self):
		"""
python3 auto_connect.py scan
Discovering devices on network...
Connecting to 192.168.1.48
Currently playing:
  Media type: Unknown
Device state: Paused
       Title: CNN Tonight With Don Lemon
      Artist: CNN
       Album: 
    Position: 50738/52200s (97.2%)
      Repeat: Off
     Shuffle: Off
Connecting to 192.168.1.47
Currently playing:
  Media type: Unknown
Device state: Paused
       Title: PBS NewsHour
      Artist: KERA
       Album: 
    Position: 46805/50400s (92.9%)
      Repeat: Off
     Shuffle: Off
		"""
		try:
			retDict = {}
			cmd = [self.pathToPython3,self.pathToPlugin+"auto_connect.py","scan"]
			if self.decideMyLog(u"GetData"): self.indiLOG.log(10,u"=========getauto_connect cmd:{}".format(cmd))
			out = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
			if self.decideMyLog(u"ReceiveData"): self.indiLOG.log(10,u"=========getauto_connect return\n{}".format(cmd, out[0]))
			if out[0].find(u"Connecting to ") 	== -1: return {}
			data = out[0].split(u"Connecting to ")[1:]
			for section in data:
				theItems = section.split("\n")
				ip		 			= theItems[0]
				retDict[ip] = {}
				if u"Media type: " 	in section: retDict[ip][u"currentlyPlaying_MediaType"] 		= section.split(u"Media type: ")[1].split("\n")[0].strip()
				if u"Device state:"	in section: retDict[ip][u"currentlyPlaying_DeviceState"]	= section.split(u"Device state: ")[1].split("\n")[0].strip()
				if u"Title: "		in section: retDict[ip][u"currentlyPlaying_Title"] 			= section.split(u"Title: ")[1].split("\n")[0].strip()
				if "Artist: " 		in section: retDict[ip][u"currentlyPlaying_Artist"] 		= section.split(u"Artist: ")[1].split("\n")[0].strip()
				if u"Album: " 		in section: retDict[ip][u"currentlyPlaying_Album"] 			= section.split(u"Album: ")[1].split("\n")[0].strip()
				if u"Position: " 	in section: retDict[ip][u"currentlyPlaying_Position"] 		= section.split(u"Position: ")[1].split("\n")[0].strip()
				if u"Repeat: " 		in section: retDict[ip][u"currentlyPlaying_Repeat"] 		= section.split(u"Repeat: ")[1].split("\n")[0].strip()
				if u"Shuffle: " 	in section: retDict[ip][u"currentlyPlaying_Shuffle"] 		= section.split(u"Shuffle: ")[1].split("\n")[0].strip()
			if self.decideMyLog(u"ReceiveData"): self.indiLOG.log(10,u"=========+++++ retDict:{}".format(json.dumps(retDict, sort_keys=True, indent=2)))



		except	Exception, e:
			if unicode(e).find(u"None") == -1:
				self.indiLOG.log(40,u"in Line {} has error={}".format(sys.exc_traceback.tb_lineno, e))
		return retDict


	def postLoop(self):

		try:
			self.pluginState   = "stop"
			indigo.server.savePluginPrefs()	
		except	Exception, e:
			if unicode(e).find(u"None") == -1:
				self.indiLOG.log(40,u"in Line {} has error={}".format(sys.exc_traceback.tb_lineno, e))
		return 


####-----------------	 ---------
	def decideMyLog(self, msgLevel):
		try:
			if msgLevel	 == u"all" or u"all" in self.debugLevel:	 return True
			if msgLevel	 == u""	  and u"all" not in self.debugLevel: return False
			if msgLevel in self.debugLevel:							 return True
			return False
		except	Exception, e:
			if unicode(e) != u"None":
				indigo.server.log( u"decideMyLog Line {} has error={}".format(sys.exc_traceback.tb_lineno, e))
		return False




####-----------------  valiable formatter for differnt log levels ---------
# call with: 
# formatter = LevelFormatter(fmt='<default log format>', level_fmts={logging.INFO: '<format string for info>'})
# handler.setFormatter(formatter)
class LevelFormatter(logging.Formatter):
	def __init__(self, fmt=None, datefmt=None, level_fmts={}, level_date={}):
		self._level_formatters = {}
		self._level_date_format = {}
		for level, format in level_fmts.items():
			# Could optionally support level names too
			self._level_formatters[level] = logging.Formatter(fmt=format, datefmt=level_date[level])
		# self._fmt will be the default format
		super(LevelFormatter, self).__init__(fmt=fmt, datefmt=datefmt)
		return

	def format(self, record):
		if record.levelno in self._level_formatters:
			return self._level_formatters[record.levelno].format(record)

		return super(LevelFormatter, self).format(record)

