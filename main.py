#!/usr/bin/python3

import json
import logging
import logging.config
from os import wait
import sys

import paho.mqtt.client as mqtt
import yaml
from apscheduler.schedulers.background import BackgroundScheduler

from bulb import BulbDevice
from plug import PlugDevice
from util import current_milli_time

scheduler = None
mqtt_client = None
config = {}
devices = {}

log = logging.getLogger("main")
tick  = current_milli_time()

def on_connect(mqtt_client, userdata, flags, rc):
    log.info(f"Connected with result code: {str(rc)}")

    if rc == 0:
        for device_id in devices:
            devices[device_id].subscribe(mqtt_client)
    else:
        sys.exit(-1)

def on_message(client, userdata, msg):
    log.debug(f"{msg.topic}: {str(msg.payload)}")

    try:
        ss = msg.topic.split('/', 3)
        if len(ss) == 3:
            re_device_id = ss[0]
            device = None
            if re_device_id in devices:
                device = devices[re_device_id]

            if device == None:
                log.warn(f"unknown device: {re_device_id}")

            elif ss[1] == 'command':
                re_cmd = ss[2]
                re_msg = msg.payload.decode('utf-8').strip()
                log.debug(f"{re_device_id}: Executing command {re_cmd}: {re_msg}")
                device.on_command(re_cmd, re_msg)

            elif ss[1] == 'config':
                if ss[2] == 'get':
                    device.on_config_get()
                elif ss[2] == 'update':
                    re_msg = msg.payload.decode('utf-8')
                    re_msg_json = json.loads(re_msg)
                    device.on_config_update(re_msg_json)

        else:
            log.warn(f"invalid topic: {msg.topic}")

    except Exception:
        log.exception(f"unable to process message of topic: {msg.topic}")
        

def on_sched():
    global devices
    global tick

    for device_id in devices:
        devices[device_id].update()

    tick  = current_milli_time() + (60 * 1000)

def on_checker():
    global tick
    global scheduler

    log.debug(f"last tick: {tick}, current tick: {current_milli_time()}")
    if current_milli_time() > tick:
        # workaround if the main scheduler got stuck
        log.error("job scheduler got stuck. exiting...")
        try:
            scheduler.shutdown(wait=False)
        finally:
            sys.exit(1)

def parse_config():
    global config
    log.info("parsing configuration...")

    with open('config.yaml') as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

    log.info("configuration read!")

    
def main():
    global devices
    global mqtt_client
    global scheduler

    logging.config.fileConfig(fname='logging.ini', disable_existing_loggers=False)

    parse_config()
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    for e in config['kasa']['devices']:
        if e['type'] == 'plug':
            devices[e['device_id']] = PlugDevice(e, mqtt_client)
        elif e['type'] == 'bulb':
            devices[e['device_id']] = BulbDevice(e, mqtt_client)
        else:
            raise Exception("invalid device type '{}' of device '{}'".format(e['type'], e['device_id']))

    scheduler = BackgroundScheduler()
    scheduler.add_job(on_sched, 'interval', seconds=config['kasa']['config']['polling_interval_sec'], misfire_grace_time=5)
    scheduler.add_job(on_checker, 'interval', minutes=1)
    scheduler.start()

    mqtt_client.connect(config['iot']['host'], config['iot']['port'], 60)
    mqtt_client.loop_forever()
    

if __name__ == "__main__":
    main()
