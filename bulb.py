
import asyncio
import logging
import json
from util import is_false, is_true 

from kasa.smartbulb import SmartBulb

log = logging.getLogger(f"main.{__name__}")

class BulbDevice:
    def __init__(self, config, mqtt):
        self.mqtt = mqtt
        self.bulb = SmartBulb(config['host'])
        self.device_id = config['device_id']

    def update(self):
        asyncio.run(self._update())

    def subscribe(self, mqtt):
        mqtt.subscribe(f"{self.device_id}/command/+")

    def publish_val(self, name, value):
        topic = f"{self.device_id}/values/{name}"
        self.mqtt.publish(topic, str(value), 0)
        log.debug('Topic: %s, Value: %s', topic, value)

    def publish_err(self, name, value):
        topic = f"{self.device_id}/errors/{name}"
        self.mqtt.publish(topic, str(value), 0)
        log.debug('Topic: %s, Error: %s', topic, value)

    def public_config(self, type, valueJson):
        topic = f"{self.device_id}/config/{type}"
        self.mqtt.publish(topic, valueJson, 0)
        log.debug('Topic: %s, Error: %s', topic, valueJson)
    
    def on_config_get(self):
        self.update()

    def on_config_update(self, partialWantJson):
        pass

    def on_command(self, cmd, msg):
        value = msg.strip().lower()
        self.update()

        try:
            if cmd == 'power_state':
                if is_true(value):
                    asyncio.run(self.bulb.turn_on())
                    self.update()
                    log.debug(f"Turning on {self.device_id}")
                elif is_false(value):
                    asyncio.run(self.bulb.turn_off())
                    self.update()
                    log.debug(f"Turning off {self.device_id}")
            elif cmd == 'color_temperature':
                color_temperature = int(msg)
                asyncio.run(self.bulb.set_color_temp(color_temperature))
                log.debug(f"Setting color temperature to {color_temperature} for {self.device_id}")
            elif cmd == 'brightness':
                brightness = int(msg)
                asyncio.run(self.bulb.set_brightness(brightness))
                log.debug(f"Setting brightness to {brightness} for {self.device_id}")
            elif cmd == 'hsv':
                h, s, v = msg.split(',')
                asyncio.run(self.bulb.set_hsv(int(h), int(s), int(v)))
                log.debug(f"Setting hsv to {h},{s},{v} for {self.device_id}")
            elif cmd == 'sync':
                self.update()
                
        except Exception as e:
            self.publish_err('command', e.__str__())

    async def _update(self):
        try:
            await self.bulb.update()

            sysinfo = await self.bulb.get_sys_info()

            # publish simple values
            self.publish_val('power_state',  'yes' if sysinfo['light_state']['on_off'] else 'no')
            self.publish_val('rssi', sysinfo['rssi'])

            light_state = sysinfo['light_state']
            if "dft_on_state" in light_state:
                light_state = light_state['dft_on_state']
                light_state['on_off'] = 0

            self.publish_val('color_temperature', light_state['color_temp'])
            self.publish_val('brightness', light_state['brightness'])
            self.publish_val('hue', light_state['hue'])
            self.publish_val('saturation', light_state['saturation'])

            pw = await self.bulb.get_emeter_realtime()
            self.publish_val('power_mw', pw['power_mw'])
            self.publish_val('power_total_wh', pw['total_wh'])

            # construct config
            del sysinfo['light_state']
            config = {}
            config['device'] = sysinfo
            config['state'] = light_state
            configJsonStr = json.dumps(config, indent=4)

            self.public_config('live', configJsonStr)
            log.debug(f"config: {configJsonStr}")

        except Exception as e:
            self.publish_err('update', e.__str__())
