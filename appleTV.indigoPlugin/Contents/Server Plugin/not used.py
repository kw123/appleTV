#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# apple tv  Plugin
#  not used anymore 


					if False:  # dont need this anymore have modified the script .py  program to also return MAC .. 
						data2 = self.getatvremoteScan(ip=ip)
						if ip in data2:
							if self.decideMyLog(u"Consumption"): self.indiLOG.log(10,u"=========getatvremoteScan result:{}".format(data2))
							if u"MRPCredentials" 		in data2[ip]: 		data[ip][u"MRPCredentials"] 	= data2[ip][u"MRPCredentials"]
							if u"AIRPLAYCredentials" 	in data2[ip]: 		data[ip][u"AIRPLAYCredentials"] = data2[ip][u"AIRPLAYCredentials"]
							if u"DMAPCredentials" 		in data2[ip]: 		data[ip][u"DMAPCredentials"] 	= data2[ip][u"DMAPCredentials"]


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
	def getPlaying(self):
		try: 
			if time.time() - self.lastGetPlaying < self.everyxSecGetPlaying: return
			self.lastGetPlaying = time.time()

			for dev in indigo.devices.iter(u"props.isAppleTV"):
				ip = dev.states[u"ip"]
				identifier = dev.states[u"identifier"]
				data = self.getscriptPlaying(identifier)
				self.fillScanIntoDevStates(dev, data)
				if self.decideMyLog(u"Consumption"): self.indiLOG.log(10,u"=========+++++ combined:{}".format(json.dumps(data, sort_keys=True, indent=2)))

		except	Exception, e:
			if unicode(e).find(u"None") == -1:
				self.indiLOG.log(40,u"in Line {} has error={}".format(sys.exc_traceback.tb_lineno, e))
		return 



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


	####-----------------	 ---------
	### not used anymore 
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
			if len(out[0]) < 5:					return retDict
			data = json.loads(out[0])
			if u"result" not  in data:			return retDict
			retDict[u"result"] = data[u"result"]
			if data[u"result"] != u"success":	return retDict
			return retDict
			if self.decideMyLog(u"ReceiveData"): self.indiLOG.log(10,u"=========getscriptPlaying retDict:{}".format(json.dumps(data, sort_keys=True, indent=2)))

		except	Exception, e:
			if unicode(e).find(u"None") == -1:
				self.indiLOG.log(40,u"in Line {} has error={}".format(sys.exc_traceback.tb_lineno, e))
				if not self.decideMyLog(u"ReceiveData"): self.indiLOG.log(10,u"=========getscriptScan out[0]:{}".format(out[0]))
				if     self.decideMyLog(u"ReceiveData"): self.indiLOG.log(10,u"=========getscriptScan out[1]:{}".format(out[1]))
		return retDict

