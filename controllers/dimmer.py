import Domoticz
from devices_manager import DevicesManager


class Dimmer:
    def __init__(self, devices_manager, mode):
        self.mode = mode
        self.devices_manager = devices_manager

    def checkDevices(self):
        for unit in range(1, 6):
            if not self.devices_manager.has_device(unit):
                Domoticz.Debug("Create Dimmer Device #" + str(unit))
                self.devices_manager.create_device(name="Channel #" + str(unit), unit=unit, type=244, sub_type=73, switch_type=7)

    def onMqttMessage(self, topic, payload):
        if "Channel" not in payload:
            return

        for unit, level in enumerate(payload["Channel"], start=1):
            Domoticz.Debug("Unit {}: {}".format(unit, level))

            device = self.devices_manager.get_device_by_unit(unit)
            n_value = 1 if level > 0 else 0
            s_value = str(level)

            if device.nValue != n_value or device.sValue != s_value:
                device.Update(nValue=n_value, sValue=s_value)

    def onCommand(self, mqttClient, unit, command, level, color):
        topic = "cmnd/" + self.mode + "/Channel" + str(unit)

        if (command == "Off"):
            mqttClient.publish(topic, "0")
        elif (command == "On"): 
            mqttClient.publish(topic, str(level))
        elif (command == "Set Level"):
            mqttClient.publish(topic, str(level))