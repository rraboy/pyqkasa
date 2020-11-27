#!/usr/bin/python3

import paho.mqtt.client as mqtt
import asyncio
import time
import os
import sys
import yaml

from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from kasa import SmartPlug
from device import PlugDevice

mqtt_client = None
config = {}
devices = {}

def on_connect(mqtt_client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    if rc == 0:
        for device_id in devices:
            devices[device_id].subscribe(mqtt_client)
    else:
        sys.exit(-1)

def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))
    for device_id in devices:
        if msg.topic.startswith(device_id + '/'):
            devices[device_id].on_message(msg.payload.decode('utf-8'))


def sched():
    global devices

    for device_id in devices:
        devices[device_id].update()

def parse_config():
    global config
    print("parsing configuration...")

    with open('config.yaml') as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
    
def main():
    global devices
    global mqtt_client

    parse_config()
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    for e in config['kasa']['devices']:
        devices[e['device_id']] = PlugDevice(e, mqtt_client)


    scheduler = BackgroundScheduler()
    scheduler.add_job(sched, 'interval', seconds=config['kasa']['config']['polling_interval_sec'])
    scheduler.start()

    mqtt_client.connect(config['iot']['host'], config['iot']['port'], 60)
    mqtt_client.loop_forever()
    

if __name__ == "__main__":
    main()
