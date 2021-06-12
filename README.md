=================== HELP for appleTV plugin===========================  
##  **credits**    
This plugin is build on top of AVTpy by Postlund, see https://github.com/postlund/pyatv  
  
##  STEPS TO MAKE IT WORK 
1. INSTALL X-CODE  in a terminal window  
   xcode-select —install  
  
2. now test if python3 is installed:   
   open terminal and type python3    and exit() if its starts sucessfully 
2.1 if python3 is not installed:   
    INSTALL PYTHON3 - if you don't have it on your mac (do not use home-brew)   
go to eg https://www.python.org/downloads/release/python-392/  
and download the 64 bit installer and install (all point and click)  
  
path to python either    /usr/local/bin/python3  for 10.14.x and earlier (w pip3 install)  
                   or    /usr/bin/python3        for 11.x and later)  
Try 'which python3' in a terminal window to check for path on your MAC)  
  
3. DOWNLOAD/INSTALL pyatv  in a terminal window  
    sudo pip3 install pyatv  
  
3.1 you might need to install the following if pytv shows errors like:  
  ModuleNotFoundError: No module named 'pendulum'  
    sudo pip3 install pendulum 
    sudo pip3 install bidict  
    sudo pip3 install more_itertools  
    sudo pip3 install bitstruct  
  
##  WHAT DOES THE PLUGIN DO:  
1. it scans the local network for apple TVs with atvscript.py scan   
   for each apple tv it finds it will create a correcponding indigo device  
   you can exclude ip numbers from being considered  
2. then is lauchnes a listener for any change of channel, volume, dev state etc and populates the indigo dev states accordingly   
3. every xx minutes it will rescan for new apple TVs - or you can manually scan in plugin/menu  
4. you can send predefined commands selectable from a list in menu or action to the apple TVs  
5. you can send free text commands in menu or action to the apple TVs, see below for list  
6. you can set certain IP numbers to be ignored (in menu), change ip number / mac# of an apple device in device edit if that has changed  
-- not yet implemented: play music / video on apple TV. That requires to sync a pin between the apple TV and the plugin 
  
##  Possible things that can go wrong:   
   dev state: 'Unclosed client session' or something like it  
      try to use iphone remote app to connect to the appleTV. If that does not work, a power cycle/restart of the appleTV should fix it  
  
## AVAILABE COMMANDS IN MENU AND ACTION   
  
### RREMOTE CONTROLL COMMANDS:  
   - down - Press key down  
   - home - Press key home  
   - home_hold - Hold key home  
   - left - Press key left  
   - menu - Press key menu  
   - next - Press key next  
   - pause - Press key play  
   - play - Press key play  
   - play_pause - Toggle between play and pause  
   - previous - Press key previous  
   - right - Press key right  
   - select - Press key select  
   - set_position - Seek in the current playing media  
   - set_repeat - Change repeat state  
   - set_shuffle - Change shuffle mode to on or off  
   - skip_backward - Skip backwards a time interval  
   - skip_forward - Skip forward a time interval  
   - stop - Press key stop  
   - suspend - Suspend the device  
   - top_menu - Go to main menu (long press menu)  
   - up - Press key up  
   - volume_down - Press key volume down  
   - volume_up - Press key volume up  
   - delay=xxxx - Sleep for a certain amount in milliseconds  before next command eg when you send 2 or more commands 
  
### POWER COMMANDS:  
   - power_state - Return device power state  
   - turn_off - Turn device off  
   - turn_on - Turn device on  
  
### METADATA COMMANDS, PRINTED TO LOG  
   - app - Return information about current app playing something  
   - artwork - Return artwork for what is currently playing (or None)  
   - artwork_id - Return a unique identifier for current artwork  
   - device_id - Return a unique identifier for current device  
   - playing - Return what is currently playing   
  
### PLAYING COMMANDS:  - print result to log  
   - album - Album of the currently playing song  
   - artist - Artist of the currently playing song  
   - device_state - Device state, e.g. playing or paused  
   - genre - Genre of the currently playing song  
   - hash - Create a unique hash for what is currently playing  
   - media_type - Type of media is currently playing, e.g. video, music  
   - position - Position in the playing media (seconds)  
   - repeat - Repeat mode  
   - shuffle - If shuffle is enabled or not  
   - title - Title of the current media, e.g. movie or song name  
   - total_time - Total play time in seconds   
  
### DEVICE COMMANDS:  
   - artwork_save - Download artwork and save it to artwork.png  
   - features - Print a list of all features and options  
  
## NOT IMPLEMENTED YET, needs pairing --  
### AirPlay commands:  
   - play_url - Play media from an URL on the device   
  
## DETAILED logs are in  
   ../Perceptive Automation/Indigo x.y/Logs/com.karlwachs.appleTV/plugin.log   

