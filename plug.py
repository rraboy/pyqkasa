
import asyncio
import logging
import json 

from kasa import SmartPlug

log = logging.getLogger(f"main.{__name__}")

class PlugDevice:
    def __init__(self, config, mqtt):
        self.mqtt = mqtt
        self.plug = SmartPlug(config['host'])
        self.device_id = config['device_id']

    def update(self):
        asyncio.run(self._update())

    def subscribe(self, mqtt):
        mqtt.subscribe(f"{self.device_id}/command/+")

    def publish_val(self, name, value):
        topic = f"{self.device_id}/values/{name}"
        self.mqtt.publish(topic, str(value), 1)
        log.debug('Topic: %s, Value: %s', topic, value)

    def on_command(self, cmd, msg):
        value = msg.strip().lower()

        if cmd == 'power_state':
            if value == "true" or value == "yes":
                asyncio.run(self.plug.turn_on())
                self.update()
                log.debug(f"Turning on {self.device_id}")
            elif value == "false" or value == "no":
                asyncio.run(self.plug.turn_off())
                self.update()
                log.debug(f"Turning off {self.device_id}")
        elif cmd == 'sync':
            self.update()

    async def _update(self):
        await self.plug.update()
        sysinfo = await self.plug.get_sys_info()
        self.publish_val('power_state', self.plug.is_on)
        self.publish_val('sys_info', json.dumps(sysinfo))
        self.publish_val('rssi', sysinfo['rssi'])
