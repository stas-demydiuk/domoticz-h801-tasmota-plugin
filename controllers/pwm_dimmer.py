import Domoticz
from devices_manager import DevicesManager


class PwmDimmer:
    def __init__(self, devices_manager, mode):
        self.mode = mode
        self.devices_manager = devices_manager

    def checkDevices(self):
        for unit in range(1, 6):
            if not self.devices_manager.has_device(unit):
                Domoticz.Debug("Create Dimmer Device #" + str(unit))
                self.devices_manager.create_device(name="Channel #" + str(unit), unit=unit, type=244, sub_type=73, switch_type=7)

    def onMqttMessage(self, topic, payload):
        for unit in range(1, 6):
            power_key = "POWER" + str(unit)
            level_key = "Channel" + str(unit)

            if (power_key) not in payload:
                continue

            device = self.devices_manager.get_device_by_unit(unit)
            n_value = 1 if payload[power_key] == "ON" else 0
            s_value = str(payload[level_key]) if level_key in payload else device.sValue

            if device.nValue != n_value or device.sValue != s_value:
                device.Update(nValue=n_value, sValue=s_value)

    def onCommand(self, mqttClient, unit, command, level, color):
        cmd = command.upper()

        if cmd == 'ON' or cmd == 'OFF':
            topic = "cmnd/" + self.mode + "/Power" + str(unit)
            mqttClient.publish(topic, cmd)

        if cmd == 'SET LEVEL':
            topic = "cmnd/" + self.mode + "/Channel" + str(unit)
            mqttClient.publish(topic, str(level))