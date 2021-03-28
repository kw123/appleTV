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
_debugAreas					= [u"GetData",u"ReceiveData",u"Consumption",u"Basic",u"all",u"Special","Threads"]
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

		self.statesToATVMapppingFromScan = {
					 u"currentlyPlaying_MediaType":		u"media_type"
					,u"currentlyPlaying_DeviceState":	u"device_state"
					,u"currentlyPlaying_Title":  		u"title"
					,u"currentlyPlaying_Artist":		u"artist"
					,u"currentlyPlaying_Album": 		u"album"
					,u"currentlyPlaying_Position":		u"position"
					,u"currentlyPlaying_Repeat":		u"repeat"
					,u"currentlyPlaying_Shuffle":		u"shuffle"
					,u"currentlyPlaying_Repeat":		u"repeat"
					,u"currentlyPlaying_TotalTime":		u"total_time"
					,u"currentlyPlaying_Genre":			u"genre"
					,u"currentlyPlaying_App":			u"app"
					,u"currentlyPlaying_AppId":			u"app_id"
					,u"PowerState":						u"power_state"
					}
		self.statesToATVMapppingForNewDevs = {
					 u"deepSleep":			u"deepSleep"
					,u"name":				u"name"
					,u"MAC":  				u"MAC"
					,u"model":				u"model"
					,u"MRPPort": 			u"MRPPort"
					#,u"MRPCredentials":		u"MRPCredentials"
					,u"AIRPLAYPort":		u"AIRPLAYPort"
					#,u"AIRPLAYCredentials":	u"AIRPLAYCredentials"
					,u"DMAPPort":			u"DMAPPort"
					#,u"DMAPCredentials":	u"DMAPCredentials"
					,u"identifier":			u"identifier"
					}


		
####

	####-----------------			  ---------
	def __del__(self):
		indigo.PluginBase.__del__(self)

	###########################		INIT	## START ########################

	####----------------- @ startup set global parameters, create directories etc ---------
	def startup(self):
		if not checkIndigoPluginName(self, indigo): 
			exit() 

		self.pluginState 						= "init"
		self.scanThreadsForPush 				= {}
		self.updateStatesAfterDevEditSave						= {}


		self.debugLevel = []
		for d in _debugAreas:
			if self.pluginPrefs.get(u"debug"+d, False): self.debugLevel.append(d)


		self.ignoreDevices						= json.loads(self.pluginPrefs.get("ignoreDevices","{}"))


		self.everyxSecGetNewDevices				= float(self.pluginPrefs.get("everyxSecGetNewDevices",3600))
		self.everyxSeccheckIfThreadIsRunning	= 30

		self.pathToPython3 						= self.pluginPrefs.get("pathToPython3", "/usr/local/bin/python3")
		self.indiLOG.log(20,  u"path To python3                {}".format(self.pathToPython3))
		self.indiLOG.log(20,  u"check for new devices every    {:.0f} minutes".format(self.everyxSecGetNewDevices/60))

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
		if self.decideMyLog(u"Basic"): self.indiLOG.log(10,u"starting device:  {}  {}  {}".format(dev.name, dev.id, dev.states[u"MAC"]))

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

			try: 	self.everyxSecGetNewDevices				= float(valuesDict["everyxSecGetNewDevices"])
			except: valuesDict["everyxSecGetNewDevices"] 	= unicode(int(self.everyxSecGetNewDevices))
			self.pathToPython3						= valuesDict["pathToPython3"]

			self.indiLOG.log(20,  u"check for new devices every     {:.0f} minutes".format(self.everyxSecGetNewDevices/60))
			self.indiLOG.log(20,  u"path To python3                 {}".format(self.pathToPython3))


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
			self.updateStatesAfterDevEditSave = {devId:{}}
			if valuesDict["overwritePIN"] != dev.states["pin"]:
				self.updateStatesAfterDevEditSave[devId]["pin"] = valuesDict["overwritePIN"]
			if valuesDict["overwriteIP"] != dev.states["ip"] 	and self.isValidIP(valuesDict["overwriteIP"]):
				self.updateStatesAfterDevEditSave[devId]["ip"] = valuesDict["overwriteIP"]
			if valuesDict["overwriteMAC"] != dev.states["MAC"] and self.isValidMAC(valuesDict["overwriteMAC"]):
				self.updateStatesAfterDevEditSave[devId]["MAC"] = valuesDict["overwriteMAC"]
			return True, valuesDict
		except	Exception, e:
			if unicode(e).find(u"None") == -1:
				self.indiLOG.log(40,u"in Line {} has error={}".format(sys.exc_traceback.tb_lineno, e) )
			return (False, valuesDict, valuesDict)

	####-----------------	 ---------
	def printConfigMenu(self,  valuesDict, typeId):
		out =  u"\n=================== parameter, devices used, set ..==========================="
		out += u"\nParameters -----------"
		out += u"\npath To python3            : {}".format(self.pathToPython3)
		out += u"\ncheck for new devices every: {:.0f} minutes".format(self.everyxSecGetNewDevices/60)
		out += u"\nDevices --------------"
		for dev in indigo.devices.iter(u"props.isAppleTV"):
			out += u"\n{}; id:{}; enabled:{}; ignored:{}".format(dev.name, dev.id, dev.enabled, dev.states["ip"] in self.ignoreDevices)
			for key, value in dev.states.items():
				out += u"\n    {:30s}: {}".format(key, value)
		out += u"\n==============================================================================\n"
		self.indiLOG.log(20,out)
		return valuesDict

	####-----------------	 ---------
	def ignoreDevicesCALLBACK(self,  valuesDict, typeId):
		try:
			if "device" in valuesDict:
				if self.isValidIP(valuesDict["device"]):
					self.ignoreDevices[valuesDict["device"]] = True
					self.pluginPrefs["ignoreDevices"] = json.dumps(self.ignoreDevices)
		except	Exception, e:
			if unicode(e).find(u"None") == -1:
				self.indiLOG.log(40,u"in Line {} has error={}".format(sys.exc_traceback.tb_lineno, e) )
			return (False, valuesDict, valuesDict)
		return valuesDict

	####-----------------	 ---------
	def unignoreDevicesCALLBACK(self,  valuesDict, typeId):
		try:
			if "device" in valuesDict:
				if self.isValidIP(valuesDict["device"]):
					if valuesDict["device"] in self.ignoreDevices:
						del self.ignoreDevices[valuesDict["device"]]
						self.pluginPrefs["ignoreDevices"] = json.dumps(self.ignoreDevices)
		except	Exception, e:
			if unicode(e).find(u"None") == -1:
				self.indiLOG.log(40,u"in Line {} has error={}".format(sys.exc_traceback.tb_lineno, e) )
			return (False, valuesDict, valuesDict)
		return valuesDict



	####-----------------	 ---------
	def getNewDevicesCALLBACK(self,  valuesDict, typeId):
		self.lastGetNewDevices = 0
		return valuesDict



	####-----------------	 ---------
	def filterAppleTV(self, filter, valuesDict, typeId, xx=""):
		try:
			xList = []
			for dev in indigo.devices.iter(u"props.isAppleTV"):
				if dev.enabled:
					xList.append([dev.id,dev.name])
		except	Exception, e:
			if unicode(e).find(u"None") == -1:
				self.indiLOG.log(40,u"in Line {} has error={}".format(sys.exc_traceback.tb_lineno, e) )
			return []
		return xList
	####-----------------	 ---------
	def execCommandToAppleTVCALLBACKaction(self, valuesDict, typeId):
		return self.execCommandToAppleTVCALLBACK(valuesDict.props,typeId)
	####-----------------	 ---------
	def execCommandToAppleTVCALLBACK(self, valuesDict, typId):
		try:
			cc = valuesDict["command"].split(";")
			dev = indigo.devices[int(valuesDict["appleTV"])]
			cmd = [self.pathToPython3,self.pathToPlugin+"atvremote.py", "-i", dev.states["MAC"], cc[0]]
			if cc[1] == "":
				out = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
				if self.decideMyLog(u"Special"): self.indiLOG.log(10,u"execCommandToAppleTVCALLBACK command:{}".format(cmd))
			else:
				out = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()[0].strip()
				if self.decideMyLog(u"Special"): self.indiLOG.log(10,u"execCommandToAppleTVCALLBACK ret from command:{}\n{}".format(cmd, out))
				retVal = {"PowerState.On":"on","PowerState.Off":"off"}
				val = retVal.get(out,"")
				self.fillScanIntoDevStates(dev, {cc[1]:val})
		except	Exception, e:
			if unicode(e).find(u"None") == -1:
				self.indiLOG.log(40,u"in Line {} has error={}".format(sys.exc_traceback.tb_lineno, e) )
			return  valuesDict
		return  valuesDict


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

		self.lastGetNewDevices	= 0
		self.lastcheckIfThreadIsRunning = 0
		self.loopCount 			= 0

		try:
			while True:
				self.loopCount +=1
				if self.decideMyLog(u"Basic"):self.indiLOG.log(10,u"in loop #{}".format(self.loopCount))
				self.getNewDevices()
				self.checkIfThreadIsRunning()
	
				for ii in range(10):
					self.updateChangedStatesInDeviceEdit()
					self.sleep(1)


		except	Exception, e:
			if unicode(e).find(u"None") == -1:
				self.indiLOG.log(40,u"in Line {} has error={}".format(sys.exc_traceback.tb_lineno, e))

		self.postLoop()


	def postLoop(self):

		try:
			self.pluginState   = "stop"
			self.pluginPrefs["ignoreDevices"] = json.dumps(self.ignoreDevices)
			indigo.server.savePluginPrefs()	
		except	Exception, e:
			if unicode(e).find(u"None") == -1:
				self.indiLOG.log(40,u"in Line {} has error={}".format(sys.exc_traceback.tb_lineno, e))
		return 


	###########################	   exec the loop  ############################
	####-----------------	 ---------
	def updateChangedStatesInDeviceEdit(self):
		try:
			if self.updateStatesAfterDevEditSave != {}:
				for devId in self.updateStatesAfterDevEditSave:
					if self.updateStatesAfterDevEditSave[int(devId)] != {}:
						dev = indigo.devices[devId]
						for state in self.updateStatesAfterDevEditSave[int(devId)]:
							if state == "ip":
								newIp = self.updateStatesAfterDevEditSave[devId][state]
								oldIP = dev.states["ip"]
								self.stopThreadsForPush(oldIP)
								self.indiLOG.log(10,u"resetting ip:{} to new ip:{}".format(oldIP, newIp))
								self.stopThreadsForPush(oldIP)
								self.sleep(5) # wait for old tyhread to stop, then delete reference to it 
								del self.scanThreadsForPush[oldIP]
								self.startThreadsForPush(dev.id, newIp)
								# update state and address with new IP
								props = dev.pluginProps
								props["address"] = self.fixIP(newIp)
								dev.replacePluginPropsOnServer(props)
								dev = indigo.devices[dev.id]
								dev.updateStateOnServer(state, newIp )
							else:
								dev.updateStateOnServer(state, self.updateStatesAfterDevEditSave[devId][state] )

				self.updateStatesAfterDevEditSave  = {}

		except	Exception, e:
			if unicode(e).find(u"None") == -1:
				self.indiLOG.log(40,u"in Line {} has error={}".format(sys.exc_traceback.tb_lineno, e))
		return 


	####-----------------	 ---------
	def checkIfThreadIsRunning(self, force=False):

		try:
			if time.time() - self.lastcheckIfThreadIsRunning < self.everyxSeccheckIfThreadIsRunning and not Force: return

			self.lastcheckIfThreadIsRunnings = time.time()
		
			for dev in indigo.devices.iter(u"props.isAppleTV"):
				if not dev.enabled:
					self.stopThreadsForPush(ip)
				else:
					ip = dev.states[u"ip"]
					if ip not in self.ignoreDevices:
						if ip not in self.scanThreadsForPush:
							self.startThreadsForPush(dev.id, ip)
							self.sleep(0.5)

			for ip in self.scanThreadsForPush:
				try:
					indigo.devices[int(self.scanThreadsForPush[ip]["devId"])]
				except:
					self.stopThreadsForPush(ip)
					

		except	Exception, e:
			if unicode(e).find(u"None") == -1:
				self.indiLOG.log(40,u"in Line {} has error={}".format(sys.exc_traceback.tb_lineno, e))
		return 
				



	####-----------------	 ---------
	def startThreadsForPush(self, devId, ip):
		try:
			if ip in self.ignoreDevices: return 
			if ip not in self.scanThreadsForPush:
				self.scanThreadsForPush[ip] = {}
				self.scanThreadsForPush[ip]["status"] = "starting"
				self.scanThreadsForPush[ip]["devId"] = devId
				self.scanThreadsForPush[ip]["thread"] = threading.Thread(name=u'listenToDevices', target=self.listenToDevices, args=(ip,devId,))
				self.scanThreadsForPush[ip]["thread"].start()
			else:
				self.indiLOG.log(10,u"startThreadsForPush ip{}, already defined, check if exist, status:{}".format(ip, self.scanThreadsForPush[ip]["status"] ))
				if self.scanThreadsForPush[ip]["status"] != "started":
					self.indiLOG.log(10,u"startThreadsForPush ip{}, already defined, re-launching".format(ip))
					self.scanThreadsForPush[ip]["status"] = "starting"
					self.scanThreadsForPush[ip]["devId"] = devId
					self.scanThreadsForPush[ip]["thread"] = threading.Thread(name=u'listenToDevices', target=self.listenToDevices, args=(ip,devId,))
					self.scanThreadsForPush[ip]["thread"].start()

				
		except	Exception, e:
			if unicode(e).find(u"None") == -1:
				self.indiLOG.log(40,u"in Line {} has error={}".format(sys.exc_traceback.tb_lineno, e))
		return 

	####-----------------	 ---------
	def stopThreadsForPush(self, ip):
		try:
				if ip not in self.scanThreadsForPush: return 
				self.scanThreadsForPush[ip]["status"] = "stop"
		except	Exception, e:
			if unicode(e).find(u"None") == -1:
				self.indiLOG.log(40,u"in Line {} has error={}".format(sys.exc_traceback.tb_lineno, e))
		return 


	####-----------------	 ---------
	def listenToDevices(self, ip, devId):

		try:

			self.scanThreadsForPush[ip]["status"] = "started"
			self.scanThreadsForPush[ip]["lastRead"] = time.time()
			ListenProcessFileHandle = ""
			msgSleep = 1
			newlinesFromServer = ""
			restartListenerAfterSecWithNoMessages = 600.
			while True:
				if ip in self.ignoreDevices:  
					try:	self.killPidIfRunning(ip, function="push_updates")
					except:	pass
					return
				# stop thread when asked to
				if self.pluginState == "stop" or self.scanThreadsForPush[ip]["status"] == "stop": 
					try:	self.killPidIfRunning(ip, function="push_updates")
					except:	pass
					break
				self.sleep(msgSleep)
				msgSleep = min(0.5,msgSleep)

				# restart the listener process after xx secs  w/o any message
				if time.time() - self.scanThreadsForPush[ip]["lastRead"] > restartListenerAfterSecWithNoMessages:
					try:	self.killPidIfRunning(ip, function="push_updates" )
					except:	pass
					ListenProcessFileHandle = ""
					self.sleep(5)

				# restart the listener process 
				if ListenProcessFileHandle == "" or self.scanThreadsForPush[ip]["status"] == "restart":
					cmd = [self.pathToPython3, self.pathToPlugin+"atvscript.py","-s", ip, "push_updates"]
					if self.decideMyLog(u"Threads"): self.indiLOG.log(10,"=== listenToDevices  ip:{}, (re)starting listener w cmd:{}".format(ip, cmd))
					ListenProcessFileHandle = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
					msg = unicode(ListenProcessFileHandle.stderr)
					if msg.find(u"open file") == -1:	# try this again
						self.indiLOG.log(40,u"IP#: {}; error connecting {}".formaat(ip, msg) )
						self.sleep(20)
						ListenProcessFileHandle = ""
						continue
					flags = fcntl.fcntl(ListenProcessFileHandle.stdout, fcntl.F_GETFL)  # get current p.stdout flags
					fcntl.fcntl(ListenProcessFileHandle.stdout, fcntl.F_SETFL, flags | os.O_NONBLOCK)
					if self.decideMyLog(u"Threads"): self.indiLOG.log(10,"=== listenToDevices  ip:{}, (re)started listener".format(ip))
					self.scanThreadsForPush[ip]["lastRead"] = time.time()
				## sucessful?
				if ListenProcessFileHandle == "": continue 

				## read data from input stream
				try: 
					lfs = ""
					lfs = os.read(ListenProcessFileHandle.stdout.fileno(),4096).decode(u"utf8") 
					newlinesFromServer += unicode(lfs) 
					if newlinesFromServer != "":
						self.scanThreadsForPush[ip]["alive"] = time.time()
					else: continue
				except	Exception, e:
					if unicode(e).find(u"[Errno 35]") == -1:	 # "Errno 35" is the normal response if no data, if other error stop and restart
						if unicode(e).find(u"None") == -1:
							out = u"os.read(ListenProcessFileHandle.stdout.fileno())  in Line {} has error={}\n ip:{}  type: {}".format(sys.exc_traceback.tb_lineno, e, ipNumber,uType )
							try: out+= u"fileNo: {}".format(ListenProcessFileHandle.stdout.fileno() )
							except: pass
							if unicode(e).find(u"[Errno 22]") > -1:  # "Errno 22" is  general read error "wrong parameter"
								out+= u"\n ..      try lowering/increasing read buffer parameter in config" 
								if self.decideMyLog(u"Threads"):self.indiLOG.log(30,out)
							else:
								if self.decideMyLog(u"Threads"):self.indiLOG.log(40,out)
								if self.decideMyLog(u"Threads"):self.indiLOG.log(40,lfs)
				## anything received?
				if len(newlinesFromServer) < 3: continue

				if self.decideMyLog(u"Threads"):self.indiLOG.log(10,"=== listenToDevices  ip:{}, newlines:{}".format(ip, newlinesFromServer))
				## try tu onpack it 
				try: 
					""" when apple tv is off, then restart
					{"result": "failure", "datetime": "2021-03-27T15:04:37.495967-05:00", "exception": "[Errno 60] Operation timed out", "stacktrace": "Traceback (most recent call last):\n  File \"/Library/Frameworks/Python.framework/Versions/3.9/lib/python3.9/asyncio/selector_events.py\", line 856, in _read_ready__data_received\n    data = self._sock.recv(self.max_size)\nTimeoutError: [Errno 60] Operation timed out\n", "connection": "lost"}
					{"result": "success", "datetime": "2021-03-27T15:04:37.500189-05:00", "push_updates": "finished"}
					{"result": "failure", "datetime": "2021-03-27T15:04:37.517832-05:00", "error": "Task was destroyed but it is pending!"}
					"""
					lines = (newlinesFromServer.strip("\n")).split("\n")
					for line in lines:
						#self.indiLOG.log(10,"=== listenToDevices  items:{}".format(xx))
						js = json.loads(line)
						if ( ( "connection"  in js and js["connection"]  == "closed") 				or
							 ( u"error"  	 in js and js[u"error"] 	 == u"device_not_found") 	or 
							 ( u"connection" in js and js[u"connection"] == u"lost") 				or
							 ( u"exception"  in js and js[u"exception"].find(u"timed out") >-1)  
							):
							if self.decideMyLog(u"Threads"):self.indiLOG.log(10,"=== listenToDevices  ip:{}, connection lost:{}".format(ip, newlinesFromServer))
							try:	self.killPidIfRunning(ip, function="push_updates")
							except:	pass
							ListenProcessFileHandle = "" # == restart
							msgSleep = 5
						## send result to fill device states
						self.fillScanIntoDevStates(indigo.devices[devId],js )
						newlinesFromServer = ""
						self.scanThreadsForPush[ip]["lastRead"] = time.time()
				except	Exception, e:
					if unicode(e).find(u"None") == -1:
						self.indiLOG.log(40,u"in Line {} has error={}".format(sys.exc_traceback.tb_lineno, e))
		

		except	Exception, e:
			if unicode(e).find(u"None") == -1:
				self.indiLOG.log(40,u"in Line {} has error={}".format(sys.exc_traceback.tb_lineno, e))



	####-----------------	 ---------
	def killPidIfRunning(self, ip, function=""):
		if function =="":
			cmd = "ps -ef | grep '/atvscript.py' | grep '"+ip+"' | grep -v grep"
		else:
			cmd = "ps -ef | grep '/atvscript.py' | grep '"+ip+"' | grep '"+function+"' | grep -v grep"

		#if self.decideMyLog(u"Threads"): self.indiLOG.log(10,u"killing request,  for ip:{}".format(ip))
		ret = subprocess.Popen( cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()[0]
		#if self.decideMyLog(u"Threads"): self.indiLOG.log(10,u"killing   ret:{}".format(ret))

		if len(ret) < 5:
			return

		lines = ret.split("\n")
		for line in lines:
			if len(line) < 5:
				continue

			items = line.split()
			if len(items) < 5:
				continue

			pidInLine = items[1]
			try:
				cmd = "/bin/kill -9 "+pidInLine
				#if self.decideMyLog(u"Threads"): self.indiLOG.log(10,u"killing "  +pidInLine+":\n"+line )
				ret = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,shell=True).communicate()
			except	Exception, e:
				if unicode(e).find(u"None") == -1:
					self.indiLOG.log(40,u"in Line {} has error={}".format(sys.exc_traceback.tb_lineno, e))

			break

		return


	####-----------------	 ---------
	def getNewDevices(self):

		try:
			if time.time() - self.lastGetNewDevices < self.everyxSecGetNewDevices: return

			self.lastGetNewDevices = time.time()
	
			## first do a script request scan retruns a nice json	
			data = self.getscriptScan()

			if self.decideMyLog(u"Consumption"): self.indiLOG.log(10,u"=========getNewDevices scan result:{}".format(json.dumps(data, sort_keys=True, indent=2)))

			for ip in data:
				if ip in self.ignoreDevices: continue
				ipFound = False
				for dev in indigo.devices.iter(u"props.isAppleTV"):
					if u"ip" not in dev.states: continue
					if dev.states[u"ip"] == ip:
						ipFound = True
						break
				if ipFound and not dev.enabled:
					break

				#if self.decideMyLog(u"Consumption"): self.indiLOG.log(10,u"=========new dev {}, found:{}".format(ip, ipFound))

				if not ipFound:
					## if new fill some properties with atvremote,  scan does not get all parameters
					#if self.decideMyLog(u"Consumption"): self.indiLOG.log(10,u"=========new dev doing remote.py {}".format(ip))
					if u"MAC" not in data[ip]: 
						data[ip][u"MAC"] = ""
					if False:
						data2 = self.getatvremoteScan(ip=ip)
						if ip in data2:
							if self.decideMyLog(u"Consumption"): self.indiLOG.log(10,u"=========getatvremoteScan result:{}".format(data2))
							if u"MRPCredentials" 		in data2[ip]: 		data[ip][u"MRPCredentials"] 	= data2[ip][u"MRPCredentials"]
							if u"AIRPLAYCredentials" 	in data2[ip]: 		data[ip][u"AIRPLAYCredentials"] = data2[ip][u"AIRPLAYCredentials"]
							if u"DMAPCredentials" 		in data2[ip]: 		data[ip][u"DMAPCredentials"] 	= data2[ip][u"DMAPCredentials"]

					## create new indigo device
					devProps = {}
					devProps[u"isAppleTV"]					= True
					devProps[u"SupportsOnState"]			= False
					devProps[u"SupportsSensorValue"]		= False
					devProps[u"SupportsStatusRequest"]		= False
					devProps[u"AllowOnStateChange"]			= False
					devProps[u"AllowSensorValueChange"]		= False
					devProps[u"overwriteIP"]				= ip
					devProps[u"overwriteMAC"]				= data[ip][u"MAC"]
					devProps[u"overwritePIN"]				= 1234
					dev = indigo.device.create(
					protocol =		 indigo.kProtocol.Plugin,
					address =		 self.fixIP(ip),
					name =			 "appletv_" + ip,
					description =	 data[ip][u"name"],
					pluginId =		 self.pluginId,
					deviceTypeId =	 "appleTV",
					props =			 devProps)
					#folder =		 self.folderNameIDSystemID,
					dev.updateStateOnServer(u"ip",ip)
				## fille device states
				chList =[]
				for key, val in self.statesToATVMapppingForNewDevs.items():
					if self.checkIfChanged(key, val, dev.states, data[ip]): chList.append({u"key":key, u"value":data[ip][val]}) 
				for ch in chList:
					if self.decideMyLog(u"Consumption"): self.indiLOG.log(10,u"{}:  change states {}".format(dev.name, ch))

				dev.updateStatesOnServer(chList)
				## start listener process if new device
				if not ipFound:
					if ip in self.scanThreadsForPush[ip]:
						self.stopThreadsForPush(ip)
						self.sleep(4)
					self.startThreadsForPush(dev.id, ip)


		except	Exception, e:
			if unicode(e).find(u"None") == -1:
				self.indiLOG.log(40,u"in Line {} has error={}".format(sys.exc_traceback.tb_lineno, e))
	####-----------------	 ---------
	def fillScanIntoDevStates(self, dev, data):
		try:
			if self.decideMyLog(u"Consumption"): self.indiLOG.log(10,u"=========fillScanIntoDevStates  {} :{}".format(dev.name, json.dumps(data, sort_keys=True, indent=2)))
			chList =[]

			## only select changed states
			for key, val in self.statesToATVMapppingFromScan.items():
				if self.checkIfChanged(key, val, dev.states, data): chList.append({u"key":key, u"value": "" if data[val] is None else data[val]}) 

			if self.decideMyLog(u"Consumption"):
				for ch in chList:
					self.indiLOG.log(10,u"{}  change states {}".format(dev.name,ch))

			# set status 
			if "result" in data and data["result"] == "failure" and "error" in data:
					chList.append({u"key":u"status", u"value":"failure", u"uiValue":data[u"error"]}) 
					dev.updateStateImageOnServer(indigo.kStateImageSel.SensorTripped)

			elif self.statesToATVMapppingFromScan["currentlyPlaying_DeviceState"] in data and data[self.statesToATVMapppingFromScan["currentlyPlaying_DeviceState"]] == u"idle":
					dev.updateStateImageOnServer(indigo.kStateImageSel.PowerOff)
					chList.append({u"key":u"status", u"value":data[self.statesToATVMapppingFromScan["currentlyPlaying_DeviceState"]], u"uiValue":data[self.statesToATVMapppingFromScan["currentlyPlaying_DeviceState"]]}) 

			elif self.statesToATVMapppingFromScan["currentlyPlaying_DeviceState"] in data:
					dev.updateStateImageOnServer(indigo.kStateImageSel.PowerOn)
					chList.append({u"key":u"status", u"value":data[self.statesToATVMapppingFromScan["currentlyPlaying_DeviceState"]], u"uiValue":data[self.statesToATVMapppingFromScan["currentlyPlaying_DeviceState"]]}) 

			## now fill the states
			dev.updateStatesOnServer(chList)

		except	Exception, e:
			if unicode(e).find(u"None") == -1:
				self.indiLOG.log(40,u"in Line {} has error={}".format(sys.exc_traceback.tb_lineno, e))
		return 



	####-----------------	 ---------
	def checkIfChanged(self, state, atvstate, Current, New):
		try:
			if atvstate not in New or  state not in Current: return False
			#self.indiLOG.log(10,u" state:{}, ==:{}  {} -- {}".format(state, New[state] == Current[state], New[state], Current[state]))
			NewVal = "" if New[atvstate] is None else New[atvstate]
			if NewVal != Current[state]: 					return True
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
			cmd = [self.pathToPython3, self.pathToPlugin+"atvscript.py", "scan"]
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
						if u"MAC" 			in device: retDict[ip][u"MAC"] 			= device[u"MAC"]
						if u"device_info" 	in device: retDict[ip][u"model"] 		= device[u"device_info"]
						if u"deep_sleep" 	in device: retDict[ip][u"deep_sleep"] 	= device[u"deep_sleep"]
						if u"identifier"	in device: retDict[ip][u"identifier"] 	= device[u"identifier"]
						if u"services" in device:
							for service in device[u"services"]:
								if u"protocol" 	in service: 
									protocol = service[u"protocol"].upper()
									if u"port" 	in service: 
										retDict[ip][protocol+u"Port"] = service[u"port"]
			if self.decideMyLog(u"ReceiveData"): self.indiLOG.log(10,u"=========getscriptScan dict:{}".format(json.dumps(retDict, sort_keys=True, indent=2)))
			return retDict
		except	Exception, e:
			if unicode(e).find(u"None") == -1:
				self.indiLOG.log(40,u"in Line {} has error={}".format(sys.exc_traceback.tb_lineno, e))
				if self.decideMyLog(u"ReceiveData"): self.indiLOG.log(10,u"=========getscriptScan out[1]:{}".format(out[1]))
		return {}

	####-----------------	 ---------
	def getatvremoteScan(self, ip=""):
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
			if ip == "":
				cmd = [self.pathToPython3, self.pathToPlugin+"atvremote.py", "scan"]
			else:
				cmd = [self.pathToPython3, self.pathToPlugin+"atvremote.py", "--scan-hosts", ip, "scan"]

			if self.decideMyLog(u"GetData"): self.indiLOG.log(10,u"=========getatvremoteScan cmd:{}".format(cmd))
			out = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
			if self.decideMyLog(u"ReceiveData"): self.indiLOG.log(10,u"========= getatvremoteScan ret:\n{}".format(out[0]))
			if out[0].find(u"Scan Results") 	== -1: return {}
			if out[0].find(u"       Name: ") 	== -1: return {}
			data = out[0].split(u"       Name: ")[1:]
			
			for section in data:
				ip		= section.split(u"Address: ")[1].split("\n")[0].strip()
				retDict[ip] 						= {}
				theItems 							= section.split("\n")
				retDict[ip]["name"] 				= theItems[0]
				retDict[ip][u"model"] 				= section.split(u"Model/SW: ")[1].split("\n")[0].strip()
				retDict[ip][u"MAC"] 				= section.split(u"MAC: ")[1].split("\n")[0].strip()
				retDict[ip][u"deepSleep"] 			= section.split(u"Deep Sleep: ")[1].split("\n")[0].strip()
				retDict[ip][u"MRPCredentials"] 		= ""
				retDict[ip][u"AIRPLAYCredentials"] 	= ""
				retDict[ip][u"identifier"] 			= ""

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
						
			if self.decideMyLog(u"ReceiveData"): self.indiLOG.log(10,u"=========getatvremoteScan dict:{}".format(json.dumps(retDict, sort_keys=True, indent=2)))
			
		except	Exception, e:
			if unicode(e).find(u"None") == -1:
				self.indiLOG.log(40,u"in Line {} has error={}".format(sys.exc_traceback.tb_lineno, e))
		return retDict




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

