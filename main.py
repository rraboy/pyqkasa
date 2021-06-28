#!/usr/bin/python3

import paho.mqtt.client as mqtt
import asyncio
import time
import os
import sys
import yaml
import logging
import logging.config

from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from kasa import SmartPlug
from device import PlugDevice

mqtt_client = None
config = {}
devices = {}

log = logging.getLogger("main")

def on_connect(mqtt_client, userdata, flags, rc):
    log.info(f"Connected with result code: {str(rc)}")

    if rc == 0:
        for device_id in devices:
            devices[device_id].subscribe(mqtt_client)
    else:
        sys.exit(-1)

def on_message(client, userdata, msg):
    log.debug(f"{msg.topic}: {str(msg.payload)}")

    ss = msg.topic.split('/', 3)
    if len(ss) == 3:
        if ss[1] == 'command':
            re_device_id = ss[0]
            re_cmd = ss[2]
            re_msg = msg.payload.decode('utf-8').strip()
            log.debug(f"{re_device_id}: Executing command {re_cmd}: {re_msg}")
            for device_id in devices:
                if device_id == re_device_id:
                    devices[device_id].on_command(re_cmd, re_msg)
            return

    log.warn(f"invalid topic: {msg.topic}")

def on_sched():
    global devices

    for device_id in devices:
        devices[device_id].update()

def parse_config():
    global config
    log.info("parsing configuration...")

    with open('config.yaml') as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

    log.info("configuration read!")
    
def main():
    global devices
    global mqtt_client

    logging.config.fileConfig(fname='logging.ini', disable_existing_loggers=False)

    parse_config()
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    for e in config['kasa']['devices']:
        if e['type'] == 'plug':
            devices[e['device_id']] = PlugDevice(e, mqtt_client)
        else:
            raise Exception("invalid device type '{}' of device '{}'".format(e['type'], e['device_id']))

    scheduler = BackgroundScheduler()
    scheduler.add_job(on_sched, 'interval', seconds=config['kasa']['config']['polling_interval_sec'])
    scheduler.start()

    mqtt_client.connect(config['iot']['host'], config['iot']['port'], 60)
    mqtt_client.loop_forever()
    

if __name__ == "__main__":
    main()
