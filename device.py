
import asyncio

from kasa import SmartPlug

class PlugDevice:
    def __init__(self, config, mqtt):
        self.mqtt = mqtt
        self.plug = SmartPlug(config['host'])
        self.device_id = config['device_id']

    def update(self):
        asyncio.run(self._update())

    def subscribe(self, mqtt):
        mqtt.subscribe(f"{self.device_id}/states/switch_on")

    def on_message(self, msg):
        value = msg.strip().lower()
        if value == "true" or value == "yes":
            print('Turning on ' + self.device_id)
            asyncio.run(self.plug.turn_on())
            self.update()
        elif value == "false" or value == "no":
            print('Turning off ' + self.device_id)
            asyncio.run(self.plug.turn_off())
            self.update()

    async def _update(self):
        await self.plug.update()
        print(self.plug.alias)
        print(self.plug.is_on)

        self.mqtt.publish(f"{self.device_id}/values/is_on", str(self.plug.is_on).lower(), 1)
