import ue9
import couchdb 
import math
import time
from thread import start_new_thread

class LabJack:
	def __init__(self, server = 'http://localhost:5984', database = 'labjack2'): 
		self.Labjack = ue9.UE9()
		self.Server = couchdb.Server(server)
		try:
			self.db = self.Server[database]
		except couchdb.ResourceNotFound:
			self.db = self.Server.create(database)
			print('new database created: '+database)
		
		self.updatefrequency = 1;
		
		newest = self.db.changes()['last_seq']
		self.changesfeed = self.db.changes(feed='continuous', heartbeat='1000', include_docs=True, since=newest,filter='Labjack/controldoc')
		
		self.ControlDoc = []

	def close(self):  # close Labjack, so you dont have to plug it out and in again.
		self.Labjack.close()

	def createView(self):
		## this function adds two views called bykey and bytime to the selected database, the views are written in javascript and are given to python in the JSON format
		## bykey is for a list of available devices
		## bytime is usefull for plotting, it looks if the device has a field "time"
		## the views are copied directly from couchdb's futon
		## a couchapp version of the views is contained in the folder views

		try:
			designdoc = self.db['_design/Labjack']
		except couchdb.ResourceNotFound:
			designdoc = {"_id" : "_design/Labjack"}
			print('new designdoc created')
		
		designdoc['views'] = { "bykey": {
		       "map": "function(doc) {\n\tfor(var i in doc) {\n\t\tif (typeof(doc[i])==\"object\") {\n\t\t\tfor(var j in doc[i]) {\n\t\t\t\temit([i,j], null);\n}}}}",
			   "reduce": "function(keys, values, rereduce) {\n  if (rereduce) {\n    return sum(values);\n  } else {\n    return values.length;\n  }\n}"\
			   },
		   "bytime": {
       "map": "function(doc) {\n\tvar UTCOffset = (new Date).getTimezoneOffset()*60;\n\tif (doc['time']) {\n\tfor(var i in doc) {\n\t\tif (typeof(doc[i]) == \"object\") {\n\t\t\tvar theTime = new Date((doc['time']+UTCOffset)*1000);\n\t\t\tvar year = theTime.getFullYear();\n\t\t\tvar month = theTime.getMonth();\n\t\t\tvar daym = theTime.getDate();\n\t\t\tvar hours = theTime.getHours();\n\t\t\tvar minutes = theTime.getMinutes();\n\t\t\tvar seconds = theTime.getSeconds();\n\t\t\tvar milliseconds = theTime.getMilliseconds();\n\t\t\tfor(var devicename in doc[i]) {\n\t\t\t\temit([i,devicename,year,month,daym,hours,minutes,seconds,milliseconds], doc[i][devicename]['value']);\n}}}}}",
       "reduce": "function(keys, values, rereduce) {\n\tvar tot = 0;\n\tvar count = 0;\n\tif (rereduce) {\n\t\tfor (var idx in values) {\n\t\t\ttot += values[idx].tot;\n\t\t\tcount += values[idx].count;\n\t\t\t}\n\t\t}\n\telse {\n\t \ttot = sum(values);\n\t\tcount = values.length;\n\t\t\n\t}\n\treturn {tot:tot, count:count, avg:tot/count};\n}"
   }}
		designdoc['filters'] = {"controldoc" : "function(doc, req) {if(doc._deleted == true) {return false;}if(doc._id == 'ControlDoc') {return true;}return false;}"}
		self.db.save(designdoc)
		print('view created and filter')
		
	def startUp(self):
		if 'ControlDoc' in self.db:
			self.ControlDoc = self.db['ControlDoc']
			for i in range(2):
				self.ControlDoc['DACs']['DAC'+str(i)]['voltage'] = round(self.Labjack.readRegister(5000+i*2),2)
			self.updatefrequency = float(self.ControlDoc['updatefrequency'])
		else:
			self.ControlDoc = { '_id' : 'ControlDoc', 'DACs' : {}, 'updatefrequency': self.updatefrequency}
			for i in range(2):
				self.ControlDoc['DACs']['DAC'+str(i)] = {'voltage' : round(self.Labjack.readRegister(5000+i*2),2)}
					
		self.db.save(self.ControlDoc)
		
	def updateAIN(self):
		print 'Update'
		newdoc = {'AINs' : {},'DACs' : {}, 'time' : time.time()}
		for i in range(4):
			newdoc['AINs']['AIN'+str(i)] = {'value' : self.ReadOutAIN(i)}
		for j in self.ControlDoc['DACs']:
			newdoc['DACs'][j] = {'value' : self.ControlDoc['DACs'][j]['voltage']}
		self.db.save(newdoc)
		time.sleep(self.updatefrequency)

	def setVoltageForDAC(self, DACNumber, voltage):
		dacaddress = 5000 + 2*DACNumber
		self.Labjack.writeRegister(dacaddress, voltage)
		
	def ReadOutAIN(self, ainNumber):
		ainaddress = 2*ainNumber
		value = self.Labjack.readRegister(ainaddress)
		return value
		
	def ChangesfeedListener(self):
		for line in self.changesfeed:
			print 'Change found'
			for t in line['doc']['DACs']:
						dacnumber = int(t[3])
						voltage = line['doc']['DACs'][t]['voltage']
						self.setVoltageForDAC(dacnumber,voltage)
						self.ControlDoc['DACs'][t]['voltage'] = voltage
						self.updatefrequency = float(line['doc']['updatefrequency'])
	
	def readOutData(self):
		self.createView() # if the someone changes the ControlDoc, this function adjusts the voltage and/or the update frequency
		self.startUp()			# looks if there is a ControlDoc, if not it creates one
		start_new_thread(self.ChangesfeedListener,()) # listens simultaneously to the changesfeed and if needed, changes the voltage or the update frequency
		while True:
			self.updateAIN()  # reads out the AINs in a specified frequency
			

LJ = LabJack()
LJ.readOutData()
		

		
		
		
		
		
		
		
		
		
