import Domoticz
import json


class ColorDimmer:
    def __init__(self, devices_manager, device_topic, channelsCount):
        self.devices_manager = devices_manager
        self.device_topic = device_topic
        self.channelsCount = channelsCount
        self.deviceType = 0xf1 # pTypeColorSwitch
        
        if (channelsCount == 3):
            self.name = 'RGB'
            self.deviceSubType = 0x02 # sTypeColor_RGB
            self.colorMode = 3        # ColorModeRGB
        elif (channelsCount == 4):    
            self.name = 'RGBW'
            self.deviceSubType = 0x06 # sTypeColor_RGB_W_Z
            self.colorMode = 4        # ColorModeCustom
        elif (channelsCount == 5):
            self.name = 'RGBWW'
            self.deviceSubType = 0x07 # sTypeColor_RGB_CW_WW_Z
            self.colorMode = 4        # ColorModeCustom

    def checkDevices(self):
        if not self.devices_manager.has_device(1):
            Domoticz.Debug("Create " + self.name + " Device")
            Domoticz.Device(Name=self.name, Unit=1, Type=self.deviceType, Subtype=self.deviceSubType, Switchtype=7).Create()
        else:
            device = self.devices_manager.get_device_by_unit(1)

            if device.Type != self.deviceType or device.SubType != self.deviceSubType:
                Domoticz.Debug("Remove unappropriate device #1")
                device.Delete()

    def onMqttMessage(self, topic, payload):
        device = self.devices_manager.get_device_by_unit(1)

        if ("Color" not in payload) or ("Dimmer" not in payload):
            if "POWER" in payload:
                nValue = 1 if payload["POWER"] == "ON" else 0

                if device.nValue != nValue:
                    device.Update(nValue=nValue, sValue=device.sValue)

            return

        colors = payload["Channel"]
        nValue = 1 if payload["POWER"] == "ON" else 0
        sValue = str(payload["Dimmer"])

        color = {}
        color["m"] = self.colorMode
        color["t"] = 0
        color["r"] = int(colors[0] * 255 / 100)
        color["g"] = int(colors[1] * 255 / 100)
        color["b"] = int(colors[2] * 255 / 100)
        color["cw"] = int(colors[3] * 255 / 100) if self.channelsCount == 4 else 0
        color["ww"] = int(colors[4] * 255 / 100) if self.channelsCount == 5 else 0

        if (device.nValue != nValue or device.sValue != sValue or json.loads(device.Color) != color):
            sColor = json.dumps(color)
            Domoticz.Debug('Updating device #' + str(device.ID))
            Domoticz.Debug('nValue: ' + str(device.nValue) + ' -> ' + str(nValue))
            Domoticz.Debug('sValue: ' + device.sValue + ' -> ' + sValue)
            Domoticz.Debug('Color: ' + device.Color + ' -> ' + sColor)
            device.Update(nValue=nValue, sValue=sValue, Color=sColor)

    def onCommand(self, mqttClient, unit, command, level, sColor):
        topic = "cmnd/" + self.device_topic + "/Power"

        if (command == "Off"):
            mqttClient.publish(topic, "Off")
        elif (command == "On"): 
            mqttClient.publish(topic, "On")
        elif (command == "Set Level"):
            mqttClient.publish("cmnd/" + self.device_topic + "/Dimmer", str(level))
        elif (command == "Set Color"):
            try:
                color = json.loads(sColor)
            except (ValueError, KeyError, TypeError) as e:
                Domoticz.Error("onCommand: Illegal color: '" + str(sColor) + "'")

            r = format(int(color["r"] * level / 100), '02X')
            g = format(int(color["g"] * level / 100), '02X')
            b = format(int(color["b"] * level / 100), '02X')
            colors = [r, g, b]

            if (self.channelsCount >= 4):
                w1 = format(int(color["cw"] * level / 100), '02X')
                colors.append(w1)

            if (self.channelsCount == 5):
                w2 = format(int(color["ww"] * level / 100), '02X')
                colors.append(w2)

            Domoticz.Debug('Set Color:' + json.dumps(colors))
            mqttClient.publish("cmnd/" + self.device_topic + "/Color", ''.join(colors))