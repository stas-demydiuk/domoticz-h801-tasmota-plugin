"""
<plugin key="TasmotaH801" name="H801 LED WiFi Controller with Tasmota firmware" version="0.0.1">
    <description>
      Plugin to control H801 LED WiFi Controlled with <a href="https://github.com/arendst/Sonoff-Tasmota">Tasmota</a> firmware<br/><br/>
      Specify MQTT server and port.<br/>
      <br/>
      Automatically creates Domoticz devices for connected device.<br/>
    </description>
    <params>
        <param field="Address" label="MQTT Server address" width="300px" required="true" default="127.0.0.1"/>
        <param field="Port" label="Port" width="300px" required="true" default="1883"/>

        <param field="Mode1" label="Device Topic" width="300px" default="sonoff"/>
        <param field="Mode2" label="Device Type" width="300px">
            <options>
                <option label="RGB" value="RGB" default="true"/>
                <option label="RGBW" value="RGBW"/>
                <option label="RGBWW" value="RGBWW"/>
                <option label="Dimmer (5x)" value="Dimmer" />
            </options>
        </param>

        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="Extra verbose" value="Verbose+"/>
                <option label="Verbose" value="Verbose"/>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal" default="true" />
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import json
import time
from mqtt import MqttClient

class Dimmer:
    def checkDevices(self):
        for unit in range(1, 6):
            if unit not in Devices:
                Domoticz.Debug("Create Dimmer Device #" + str(unit))
                Domoticz.Device(Name="Channel #" + str(unit), Unit=unit, Type=244, Subtype=73, Switchtype=7).Create()

    def onMqttMessage(self, topic, payload):
        for unit, level in enumerate(payload["Channel"], start=1):
            Domoticz.Debug("Unit {}: {}".format(unit, level))
            nValue = 1 if level > 0 else 0
            Devices[unit].Update(nValue=nValue, sValue=str(level))

    def onCommand(self, mqttClient, unit, command, level, color):
        topic = "cmnd/" + Parameters["Mode1"] + "/Channel" + str(unit)

        if (command == "Off"):
            mqttClient.Publish(topic, "0")
        elif (command == "On"): 
            mqttClient.Publish(topic, str(level))
        elif (command == "Set Level"):
            mqttClient.Publish(topic, str(level))

class ColorDimmer:
    def __init__(self, channelsCount):
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
        if 1 in Devices and (Devices[1].Type != self.deviceType or Devices[1].SubType != self.deviceSubType):
             Domoticz.Debug("Remove unappropriate device #1")
             Devices[1].Delete()

        if 1 not in Devices:
            Domoticz.Debug("Create " + self.name + " Device")
            Domoticz.Device(Name=self.name, Unit=1, Type=self.deviceType, Subtype=self.deviceSubType, Switchtype=7).Create()

    def onMqttMessage(self, topic, payload):
        if ("Color" not in payload) or ("Dimmer" not in payload):
            if ("POWER" in payload):
                nValue = 1 if payload["POWER"] == "ON" else 0
                Devices[1].Update(nValue=nValue, sValue=Devices[1].sValue)

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

        Devices[1].Update(nValue=nValue, sValue=sValue, Color=json.dumps(color))

    def onCommand(self, mqttClient, unit, command, level, sColor):
        topic = "cmnd/" + Parameters["Mode1"] + "/Power"

        if (command == "Off"):
            mqttClient.Publish(topic, "Off")
        elif (command == "On"): 
            mqttClient.Publish(topic, "On")
        elif (command == "Set Level"):
            mqttClient.Publish("cmnd/" + Parameters["Mode1"] + "/Dimmer", str(level))
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
            mqttClient.Publish("cmnd/" + Parameters["Mode1"] + "/Color", ''.join(colors))

class BasePlugin:
    mqttClient = None

    def onStart(self):
        self.debugging = Parameters["Mode6"]
        
        if self.debugging == "Verbose+":
            Domoticz.Debugging(2+4+8+16+64)
        if self.debugging == "Verbose":
            Domoticz.Debugging(2+4+8+16+64)
        if self.debugging == "Debug":
            Domoticz.Debugging(2+4+8)

        if (Parameters["Mode2"] == "Dimmer"):
            self.controller = Dimmer()
        elif (Parameters["Mode2"] == "RGB"):
            self.controller = ColorDimmer(3)
        elif (Parameters["Mode2"] == "RGBW"):
            self.controller = ColorDimmer(4)
        elif (Parameters["Mode2"] == "RGBWW"):
            self.controller = ColorDimmer(5)

        self.controller.checkDevices()

        self.topics = list(["stat/" + Parameters["Mode1"] + "/RESULT", "tele/" + Parameters["Mode1"] + "/STATE"])
        self.mqttserveraddress = Parameters["Address"].replace(" ", "")
        self.mqttserverport = Parameters["Port"].replace(" ", "")
        self.mqttClient = MqttClient(self.mqttserveraddress, self.mqttserverport, self.onMQTTConnected, self.onMQTTDisconnected, self.onMQTTPublish, self.onMQTTSubscribed)

    def checkDevices(self):
        Domoticz.Log("checkDevices called")

    def onStop(self):
        Domoticz.Log("onStop called")

    def onCommand(self, Unit, Command, Level, Color):
        Domoticz.Debug("Command: " + Command + " (" + str(Level) + ") Color:" + Color)
        self.controller.onCommand(self.mqttClient, Unit, Command, Level, Color)

    def onConnect(self, Connection, Status, Description):
        self.mqttClient.onConnect(Connection, Status, Description)

    def onDisconnect(self, Connection):
        self.mqttClient.onDisconnect(Connection)

    def onMessage(self, Connection, Data):
        self.mqttClient.onMessage(Connection, Data)

    def onHeartbeat(self):
        Domoticz.Debug("Heartbeating...")

        # Reconnect if connection has dropped
        if self.mqttClient.mqttConn is None or (not self.mqttClient.mqttConn.Connecting() and not self.mqttClient.mqttConn.Connected() or not self.mqttClient.isConnected):
            Domoticz.Debug("Reconnecting")
            self.mqttClient.Open()
        else:
            self.mqttClient.Ping()

    def onMQTTConnected(self):
        Domoticz.Debug("onMQTTConnected")
        self.mqttClient.Subscribe(self.topics)

    def onMQTTDisconnected(self):
        Domoticz.Debug("onMQTTDisconnected")

    def onMQTTSubscribed(self):
        Domoticz.Debug("onMQTTSubscribed")

    def onMQTTPublish(self, topic, rawmessage):
        Domoticz.Debug("MQTT message: " + topic + " " + str(rawmessage))

        message = ""
        try:
            message = json.loads(rawmessage.decode('utf8'))
        except ValueError:
            message = rawmessage.decode('utf8')

        if (topic in self.topics):
            self.controller.onMqttMessage(topic, message)

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()
    
def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Color):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Color)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()