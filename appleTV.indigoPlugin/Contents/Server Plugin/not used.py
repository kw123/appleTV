#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# apple tv  Plugin
#  not used anymore 

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

