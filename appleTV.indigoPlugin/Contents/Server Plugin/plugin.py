#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# apple tv  Plugin
# Developed by Karl Wachs
# karlwachs@me.com
#pyatv is maintained by postlund
#see: https://github.com/postlund/pyatv
try:
	import json
except:
	import simplejson as json

import datetime
import time
import subprocess
import fcntl
import os
import sys
import pwd
import Queue
import threading
import logging
import copy

from checkIndigoPluginName import checkIndigoPluginName 


######### set new  pluginconfig defaults
# this needs to be updated for each new property added to pluginprops. 
# indigo ignores the defaults of new properties after first load of the plugin 

kDefaultPluginPrefs = {
				"everyxSecGetNewDevices":	"86400",
				"pathToPython3":			"/usr/local/bin/python3",
				"debugGetData":				False,
				"debugConsumption":			False,
				"debugReceiveData":			False,
				"debugThreads":				False,
				"debugAction":				False,
				"debugBasic":				False,
				"debugSpecial":				False,
				"debugall":					False
				}


dataVersion = 0.1

## Static parameters, not changed in pgm
_debugAreas					= [u"GetData",u"ReceiveData",u"Consumption",u"Basic",u"all",u"Special","Threads","Action"]
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
		self.updateStatesAfterDevEditSave		= {}


		self.debugLevel = []
		for d in _debugAreas:
			if self.pluginPrefs.get(u"debug"+d, False): self.debugLevel.append(d)


		self.ignoreDevices						= json.loads(self.pluginPrefs.get("ignoreDevices","{}"))

		self.everyxSecGetNewDevices				= float(self.pluginPrefs.get("everyxSecGetNewDevices",86400))
		self.everyxSeccheckIfThreadIsRunning	= 30

		self.pathToPython3 						= self.pluginPrefs.get("pathToPython3", "/usr/local/bin/python3")
		self.indiLOG.log(20,  u"path To python3                {}".format(self.pathToPython3))
		self.indiLOG.log(20,  u"check for new devices every    {:.0f} minutes".format(self.everyxSecGetNewDevices/60))
		if not os.path.isfile(self.pathToPython3):
				self.indiLOG.log(30,u" {}  is not present on this mac, see logfile on how to install python3".format(self.pathToPython3) )
				self.printHelpMenu( {}, "")
				self.sleep(2000)
				exit(0) 

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
		if self.pluginState != u"init":
			if self.decideMyLog(u"Basic"):self.indiLOG.log(10,u"starting device:  {}  {}".format(dev.name, dev.id))

		if self.pluginState == "init":
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
			self.pathToPython3								= valuesDict["pathToPython3"]
			if not os.path.isfile(self.pathToPython3):
				self.indiLOG.log(30,u" {}  is not present on this mac, see logfile on  how to install python3".format(self.pathToPython3) )
				valuesDict["pathToPython3"] = u" does not exist"
				self.printHelpMenu( {}, "")
				return (False, valuesDict, valuesDict)

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
	def printHelpMenu(self,  valuesDict, typeId):
		out =  u"\n# =================== HELP for appleTV plugin===========================  \n"
		out += u"##  **credits**    \n"
		out += u"This plugin is build on top of AVTpy by Postlund, see https://github.com/postlund/pyatv  \n"
		out += u"  \n"
		out += u"##  STEPS TO MAKE IT WORK \n"
		out += u"1. INSTALL X-CODE  in a terminal window  \n"
		out += u"xcode-select —install  \n"
		out += u"  \n"
		out += u"2. INSTALL PYTHON3 - if you don't have it on your mac (do not use home-brew)   \n"
		out += u"go to eg https://www.python.org/downloads/release/python-392/  \n"
		out += u"and download the 64 bit installer and install (all point and click)  \n"
		out += u"  \n"
		out += u"3. DOWNLOAD/INSTALL pyatv  in a terminal window  \n"
		out += u"pip3 install pyatv  \n"
		out += u"  \n"
		out += u"path to python either    /usr/local/bin/python3  for 10.14.x and earlier (w pip3 install)  \n"
		out += u"                   or    /usr/bin/python3        for 11.x and later)  \n"
		out += u"Try 'which python3' in a terminal window to check for path on your MAC)  \n"
		out += u"  \n"
		out += u"##  WHAT DOES IT DO:  \n"
		out += u"1. it scans the local network for apple TVs with atvscript.py scan   \n"
		out += u"2. then is lauchnes a listener for any change of channel, volume, dev state etc and populates the indigo dev states accordingly   \n"
		out += u"3. every xx minutes it will rescan for new apple TVs - or you can manually scan in plugin/menu  \n"
		out += u"4. you can send predefined commands selectable from a list in menu or action to the apple TVs \n"
		out += u"5. you can send free text commands in menu or action to the apple TVs, see below for list \n"
		out += u"6. you can set certain IP numbers to be ignored, change ip number / mac# of an apple device in device edit if that has changed \n"
		out += u"-- not yet implemented: play music / video on apple TV. That requires to sync a pin between the apple TV and the plugin \n"
		out += u"  \n"
		out += u"##  Possible things that can go wrong:   \n"
		out += u"   dev state: 'Unclosed client session' or something like it  \n"
		out += u"      try to use iphone remote app to connect to the appleTV. If that does not work a power cycle appleTV should fix it  \n"
		out += u"  \n"
		out += u"## AVAILABE COMMANDS IN MENU AND ACTION   \n"
		out += u"  \n"
		out += u"### RREMOTE CONTROLL COMMANDS:  \n"
		out += u"   - down - Press key down  \n"
		out += u"   - home - Press key home  \n"
		out += u"   - home_hold - Hold key home  \n"
		out += u"   - left - Press key left  \n"
		out += u"   - menu - Press key menu  \n"
		out += u"   - next - Press key next  \n"
		out += u"   - pause - Press key play  \n"
		out += u"   - play - Press key play  \n"
		out += u"   - play_pause - Toggle between play and pause  \n"
		out += u"   - previous - Press key previous  \n"
		out += u"   - right - Press key right  \n"
		out += u"   - select - Press key select  \n"
		out += u"   - set_position - Seek in the current playing media  \n"
		out += u"   - set_repeat - Change repeat state  \n"
		out += u"   - set_shuffle - Change shuffle mode to on or off  \n"
		out += u"   - skip_backward - Skip backwards a time interval  \n"
		out += u"   - skip_forward - Skip forward a time interval  \n"
		out += u"   - stop - Press key stop  \n"
		out += u"   - suspend - Suspend the device  \n"
		out += u"   - top_menu - Go to main menu (long press menu)  \n"
		out += u"   - up - Press key up  \n"
		out += u"   - volume_down - Press key volume down  \n"
		out += u"   - volume_up - Press key volume up  \n"
		out += u"   - delay=xxxx - Sleep for a certain amount in milliseconds  before next command eg when you send 2 or more commands \n"
		out += u"  \n"
		out += u"### POWER COMMANDS:  \n"
		out += u"   - power_state - Return device power state  \n"
		out += u"   - turn_off - Turn device off  \n"
		out += u"   - turn_on - Turn device on  \n"
		out += u"  \n"
		out += u"### METADATA COMMANDS, PRINTED TO LOG  \n"
		out += u"   - app - Return information about current app playing something  \n"
		out += u"   - artwork - Return artwork for what is currently playing (or None)  \n"
		out += u"   - artwork_id - Return a unique identifier for current artwork  \n"
		out += u"   - device_id - Return a unique identifier for current device  \n"
		out += u"   - playing - Return what is currently playing   \n"
		out += u"  \n"
		out += u"### PLAYING COMMANDS:  - print result to log  \n"
		out += u"   - album - Album of the currently playing song  \n"
		out += u"   - artist - Artist of the currently playing song  \n"
		out += u"   - device_state - Device state, e.g. playing or paused  \n"
		out += u"   - genre - Genre of the currently playing song  \n"
		out += u"   - hash - Create a unique hash for what is currently playing  \n"
		out += u"   - media_type - Type of media is currently playing, e.g. video, music  \n"
		out += u"   - position - Position in the playing media (seconds)  \n"
		out += u"   - repeat - Repeat mode  \n"
		out += u"   - shuffle - If shuffle is enabled or not  \n"
		out += u"   - title - Title of the current media, e.g. movie or song name  \n"
		out += u"   - total_time - Total play time in seconds   \n"
		out += u"  \n"
		out += u"### DEVICE COMMANDS:  \n"
		out += u"   - artwork_save - Download artwork and save it to artwork.png  \n"
		out += u"   - features - Print a list of all features and options  \n"
		out += u"  \n"
		out += u"## NOT IMPLEMENTED YET, needs pairing --  \n"  
		out += u"### AirPlay commands:  \n" 
		out += u"   - play_url - Play media from an URL on the device   \n"
		out += u"  \n"
		out += u"## DETAILED logs are in  \n"
		out += u"   ../Perceptive Automation/Indigo x.y/Logs/com.karlwachs.appleTV/plugin.log   \n"
		out += u"===============================================================================  \n"

		self.indiLOG.log(20,out)
		return valuesDict

	####-----------------	 ---------
	def printConfigMenu(self,  valuesDict, typeId):
		out =  u"\n=================== parameter, devices used, set ..==========================="
		out += u"\nParameters -----------"
		out += u"\npath To python3            : {}".format(self.pathToPython3)
		out += u"\ncheck for new devices every: {:.0f} minutes".format(self.everyxSecGetNewDevices/60)
		out += u"\nignored IP numbers: {}".format(self.ignoreDevices)
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
				if self.decideMyLog(u"Action"): self.indiLOG.log(10,u"execCommandToAppleTVCALLBACK command:{}".format(cmd))
			else:
				out = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()[0].strip()
				if self.decideMyLog(u"Action"): self.indiLOG.log(10,u"execCommandToAppleTVCALLBACK ret from command:{}\n{}".format(cmd, out))
				retVal = {"PowerState.On":"on","PowerState.Off":"off"}
				val = retVal.get(out,"")
				self.fillScanIntoDevStates(dev, {cc[1]:val})
		except	Exception, e:
			if unicode(e).find(u"None") == -1:
				self.indiLOG.log(40,u"in Line {} has error={}".format(sys.exc_traceback.tb_lineno, e) )
			return  valuesDict
		return  valuesDict

	####-----------------	 ---------
	def execCommandsToAppleTVCALLBACKaction(self, valuesDict, typeId):
		return self.execCommandsToAppleTVCALLBACK(valuesDict.props,typeId)
	####-----------------	 ---------
	def execCommandsToAppleTVCALLBACK(self, valuesDict, typId):
		try:
			cc = valuesDict["command"]
			dev = indigo.devices[int(valuesDict["appleTV"])]
			cmd = [self.pathToPython3,self.pathToPlugin+"atvremote.py", "-i", dev.states["MAC"], cc]
			if self.decideMyLog(u"Action"): self.indiLOG.log(10,u"execCommandToAppleTVCALLBACK  command:{}".format(cmd))
			out = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()[0]
			self.indiLOG.log(20,u"action: {};  response:\n{}".format(cc, out))
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


####-----------------   end plugin             ---------
	def postLoop(self):
		try:
			self.pluginState   = "stop"
			self.pluginPrefs["ignoreDevices"] = json.dumps(self.ignoreDevices)
			indigo.server.savePluginPrefs()	
			time.sleep(1)
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
								self.indiLOG.log(10,u"changing for dev:{}  ip:{} to new ip:{}".format(dev.name, oldIP, newIp))
								self.stopThreadsForPush(oldIP)
								self.sleep(5) # wait for old thread to stop, then delete reference to it 
								del self.scanThreadsForPush[oldIP]
								# update state and address with new IP
								props = dev.pluginProps
								props["address"] = self.fixIP(newIp)
								dev.replacePluginPropsOnServer(props)
								dev = indigo.devices[dev.id]
								dev.updateStateOnServer(state, newIp )
								# start listening process w new ip number
								self.startThreadsForPush(dev.id, newIp)
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
	#### tbis is the thread that will contiinously listen to any changes  (playing) in apple TV devcies
	#### will update the corresponding indigo devices
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
				## check if we should stop (ignord, plugin ending, or stop command for THIS thread)
				if ip in self.ignoreDevices:  
					try:	self.killProcessIfRunning(ip, function="push_updates")
					except:	pass
					return
				# stop thread when asked to
				if self.pluginState == "stop" or self.scanThreadsForPush[ip]["status"] == "stop": 
					try:	self.killProcessIfRunning(ip, function="push_updates")
					except:	pass
					break
				self.sleep(msgSleep)
				msgSleep = min(0.5,msgSleep)

				# check if restart the listener process after xx secs  w/o any message
				if time.time() - self.scanThreadsForPush[ip]["lastRead"] > restartListenerAfterSecWithNoMessages:
					try:	self.killProcessIfRunning(ip, function="push_updates" )
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
								out+= u"\n ..      contect developer w logfile " 
								if self.decideMyLog(u"Threads"):self.indiLOG.log(30,out)
							else:
								if self.decideMyLog(u"Threads"):self.indiLOG.log(40,out)
								if self.decideMyLog(u"Threads"):self.indiLOG.log(40,lfs)
				## anything received?
				if len(newlinesFromServer) < 3: continue

				if self.decideMyLog(u"Threads"):self.indiLOG.log(10,"=== listenToDevices  ip:{}, newlines:{}".format(ip, newlinesFromServer))
				## try to onpack it 
				try: 
					lines = (newlinesFromServer.strip("\n")).split("\n")
					for line in lines:
						#self.indiLOG.log(10,"=== listenToDevices  items:{}".format(xx))
						js = json.loads(line)
						""" when apple tv is off, then restart, these are the message that we could receive
						{"result": "failure", "datetime": "2021-03-27T15:04:37.495967-05:00", "exception": "[Errno 60] Operation timed out", "stacktrace": "Traceback (most recent call last):\n  File \"/Library/Frameworks/Python.framework/Versions/3.9/lib/python3.9/asyncio/selector_events.py\", line 856, in _read_ready__data_received\n    data = self._sock.recv(self.max_size)\nTimeoutError: [Errno 60] Operation timed out\n", "connection": "lost"}
						{"result": "success", "datetime": "2021-03-27T15:04:37.500189-05:00", "push_updates": "finished"}
						{"result": "failure", "datetime": "2021-03-27T15:04:37.517832-05:00", "error": "Task was destroyed but it is pending!"}
						"""
						if ( ( "connection"  in js and js["connection"]  == "closed") 				or
							 ( u"error"  	 in js and js[u"error"] 	 == u"device_not_found") 	or 
							 ( u"connection" in js and js[u"connection"] == u"lost") 				or
							 ( u"exception"  in js and js[u"exception"].find(u"timed out") >-1)  
							):
							if self.decideMyLog(u"Threads"):self.indiLOG.log(10,"=== listenToDevices  ip:{}, connection lost:{}".format(ip, newlinesFromServer))
							try:	self.killProcessIfRunning(ip, function="push_updates")
							except:	pass
							ListenProcessFileHandle = "" # == restart
							msgSleep = 5

						## send result to fill device states
						self.fillScanIntoDevStates(indigo.devices[devId], js)
						newlinesFromServer = ""
						self.scanThreadsForPush[ip]["lastRead"] = time.time()
				except	Exception, e:
					if unicode(e).find(u"None") == -1:
						self.indiLOG.log(40,u"in Line {} has error={}".format(sys.exc_traceback.tb_lineno, e))
		

		except	Exception, e:
			if unicode(e).find(u"None") == -1:
				self.indiLOG.log(40,u"in Line {} has error={}".format(sys.exc_traceback.tb_lineno, e))



	####-----------------	 ---------
	def killProcessIfRunning(self, ip, function=""):
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
	
			## first do a script request scan, it retruns a nice json for all devices found
			data = self.getscriptScan()

			if self.decideMyLog(u"Consumption"): self.indiLOG.log(10,u"=========getNewDevices scan result:{}".format(json.dumps(data, sort_keys=True, indent=2)))

			for ip in data:
				try:
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
						#if self.decideMyLog(u"Consumption"): self.indiLOG.log(10,u"=========new dev doing remote.py {}".format(ip))
						if u"MAC" not in data[ip]: 
							data[ip][u"MAC"] = ""

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
						devProps[u"overwritePIN"]				= 1234  # not used yet, will need to add to find setup pairing
						dev = indigo.device.create(
						protocol =		 indigo.kProtocol.Plugin,
						address =		 self.fixIP(ip),
						name =			 "appletv_" + ip,
						description =	 data[ip][u"name"],
						pluginId =		 self.pluginId,
						deviceTypeId =	 "appleTV",
						props =			 devProps)
						#folder =		 self.folderNameIDSystemID,
						dev.updateStateOnServer(u"ip", ip)

					## fill device states
					chList =[]
					for key, val in self.statesToATVMapppingForNewDevs.items():
						if self.checkIfChanged(key, val, dev.states, data[ip]): chList.append({u"key":key, u"value":data[ip][val]}) 
					for ch in chList:
						if self.decideMyLog(u"Consumption"): self.indiLOG.log(10,u"{}:  change state {}".format(dev.name, ch))

					dev.updateStatesOnServer(chList)
					## start listener process if new device
					if not ipFound:
						if ip in self.scanThreadsForPush[ip]:
							self.stopThreadsForPush(ip)
							self.sleep(4)
						self.startThreadsForPush(dev.id, ip)
				except	Exception, e:
					self.indiLOG.log(40,u"in Line {} has error={}".format(sys.exc_traceback.tb_lineno, e))
					self.indiLOG.log(40,u"ip:{} data:{}".format(ip, data))


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
			else:
				pass

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
python3 atvscript.py scan   returns:
{"result": "success", "datetime": "2021-03-25T21:47:46.966942-05:00", 
"devices": [
{"name": "Bedroom", "address": "192.168.1.48", "identifier": "01F74624-B8BB-4EF9-9E9E-4A6C42EEC75F", 
  "services": [{"protocol": "mrp", "port": 49153}, {"protocol": "AIRPLAY", "port": 7000}]}, 
{"name": "Living Room", "address": "192.168.1.47", "identifier": "0721B1F4-4CE5-4EA7-86B7-BE4F2FCAAA30", 
  "services": [{"protocol": "mrp", "port": 49152}, {"protocol": "AIRPLAY", "port": 7000}]}]}
		"""
		try:
			out = "  "
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
	## not used anymore 


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

