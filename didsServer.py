#!/usr/bin/python

port = 8007
secondsMemory = 5
global staDict
print "\nDIDS Server started and listening on port:%s\n-------------------------------" % (port)

from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor
import dist_pb2
import sys
import os

from time import time
from math import *

stationlog = dist_pb2.Instance()

class Station(object):
    	"""
	class for stations seen
	"""
	def __init__(self, addr):
		self.addr = addr
		self.rssi = {}
		self.ewma = 0

class col:
	HEADER = '\033[47m'
	OKBLUE = '\033[34m'
	OKGREEN = '\033[32m'
	WARNING = '\033[33m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'

	def disable(self):
		self.HEADER = ''
		self.OKBLUE = ''
		self.OKGREEN = ''
		self.WARNING = ''
		self.FAIL = ''
		self.ENDC = ''

class ServeIDS(Protocol):
	def __init__(self):
		global staDict
		staDict = {}

	def connectionMade(self):
		"""
		run when connection is made. 
		"""
		print "connection made"

	def connectionLost(self, reason):
		print "connection lost"
	
	def dataReceived(self, data):
		""" 
		run every time a packet is recieved 
		"""
		thisTime = time()
		stationlog.ParseFromString(data)

		ip = self.transport.getPeer().__getitem__(1)
		os.system('clear')

		print col.HEADER + "-Monitored STAs from client at %s-" % (ip)
		print "-Station-" + "-"*14 + "-Link-" + "-"*2 + "-Strength-" + col.ENDC + "\n"
	        
		for station in stationlog.station:
 			
			# open log file (for use with gnuplot etc)
			f = open('/home/olan/logs/' + station.mac + '-server.txt', 'a')

  	        	# if station seen before extend rssi, else create new
			if staDict.has_key(station.mac):
               			sta = staDict.get(station.mac)
                		sta.rssi[thisTime] = station.rssi
				print " %s" % (station.mac),
            		else:
                		sta = Station(station.mac)
                		staDict[station.mac] = sta
                		sta.rssi[thisTime] = station.rssi
				print col.OKGREEN + " %s" % (station.mac) + col.ENDC,

			# if items in dictionary for longer than secondsMemory ago, delete
			for times in sta.rssi.keys():
				if times < (thisTime - secondsMemory):
					del sta.rssi[times]
				
			#check for number of rssi values seen over secondsMemory time
			rssicount = sum(len(sta.rssi[key]) for key in sta.rssi.keys())
			if rssicount is 0:
				del staDict[sta.addr]
		
			# get ewma and print some stats	
			self.smooth(sta, thisTime)	
			self.printStats(sta, rssicount)
				
         		f.write(str(thisTime) + '\t' + str(sta.ewma) + '\n')

			f.close()

	def printStats(self, sta, rssicount):
		"""just prints out some stats"""

		if rssicount >= 8*len(sta.rssi):
			print col.OKGREEN + "\tGood",
                elif 8*len(sta.rssi) > rssicount >= 1*len(sta.rssi):
			print col.WARNING + "\tOK",
                else:
                      	print col.FAIL + "\tPoor",

		if sta.ewma >= 40:
			print col.OKBLUE + "\tExcellent",
		elif sta.ewma >=20:
			print col.OKGREEN + "\tGood",
		elif sta.ewma >= 10:
			print col.WARNING + "\tOK",
		else:
			print col.FAIL + "\tPoor",
		print col.ENDC


	def smooth(self, sta, thisTime):
		"""
		Perfoms exponentially weighted moving average 
		on values

		sta is the station to perform on
		thisTime is the tim the packets were processed at 
		"""
		for times in sta.rssi:
			for rssival in sta.rssi[times]:
				# Y += alpha * (X - Y) where alpha = (1 - e^(delta(t)/T))
				sta.ewma += ( 1 - exp( -(thisTime - times + 1) / float(20) ) ) * (rssival - sta.ewma)

# Then lines are Twisted magic:
factory = Factory()
factory.protocol = ServeIDS

reactor.listenTCP(port, factory)
# run reactor
reactor.run()
