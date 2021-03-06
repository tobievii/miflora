#!/usr/bin/python
# -*- mode: python; coding: utf-8 -*-

# Scans for and reads data from Xiaomi flower monitor and publish via MQTT
# Tested on firmware version 2.6.2 &  2.6.6 & 2.9.4
# Xiaomi flower protocol & code from https://wiki.hackerspace.pl/projects:xiaomi-flora by emeryth (emeryth at hackerspace.pl)
# NB, change in the last line your mqtt server & authentication details if needed
# Author Marcel Verpaalen

import sys
from struct import unpack
import paho.mqtt.publish as publish
from gattlib import DiscoveryService, GATTRequester, GATTResponse

verbose = True

service = DiscoveryService("hci0")
devices = service.discover(15)

baseTopic = "/miflower/"
msgs=[]

for address, name in list(devices.items()):
    try:	
	if (name == "Flower mate" or name == "Flower care"):
		topic= baseTopic + address.replace(':', '') + '/'
		requester = GATTRequester(address, True)
		#Read battery and firmware version attribute
		data=requester.read_by_handle(0x0038)[0]
		battery, firmware = unpack('<xB5s',data)
		msgs.append({'topic': topic + 'battery', 'payload':battery})
		msgs.append({'topic': topic + 'firmware', 'payload':firmware})
		#Enable real-time data reading
		requester.write_by_handle(0x0033, str(bytearray([0xa0, 0x1f])))
		#Read plant data
		data=requester.read_by_handle(0x0035)[0]
		temperature, sunlight, moisture, fertility = unpack('<hxIBHxxxxxx',data)
		msgs.append({'topic': topic + 'temperature', 'payload':temperature/10.})
		msgs.append({'topic': topic + 'sunlight', 'payload':sunlight})
		msgs.append({'topic': topic + 'moisture', 'payload':moisture})
		msgs.append({'topic': topic + 'fertility', 'payload':fertility})
		if (verbose):
			print("name: {}, address: {}".format(name, address))
			print "Battery level:",battery,"%"
			print "Firmware version:",firmware
			print "Light intensity:",sunlight,"lux"
			print "Temperature:",temperature/10.," C"
			print "Soil moisture:",moisture,"%"
			print "Soil fertility:",fertility,"uS/cm"
    except:
        print "Error during reading:", sys.exc_info()[0]

if (len(msgs) > 0):
	#publish.multiple(msgs, hostname="localhost", port=1883, client_id="miflower", keepalive=60,will=None, auth=None, tls=None)
	for msg in msgs:
		publish.single(msg['topic'], payload=msg['payload'], hostname="localhost", port=1883, keepalive=60,will=None, auth=None, tls=None)
