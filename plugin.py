"""
<plugin key="TasmotaH801" name="H801 LED WiFi Controller with Tasmota firmware" version="0.1.0">
    <description>
      Plugin to control H801 LED WiFi Controlled with <a href="https://github.com/arendst/Sonoff-Tasmota">Tasmota</a> firmware<br/><br/>
      Specify MQTT server and port.<br/>
      <br/>
      Automatically creates Domoticz devices for connected device.<br/>
    </description>
    <params>
        <param field="Address" label="MQTT Server address" width="300px" required="true" default="127.0.0.1"/>
        <param field="Port" label="Port" width="300px" required="true" default="1883"/>
        <param field="Username" label="MQTT Username (optional)" width="300px" required="false" default=""/>
        <param field="Password" label="MQTT Password (optional)" width="300px" required="false" default="" password="true"/>
        <param field="Mode3" label="MQTT Client ID (optional)" width="300px" required="false" default=""/>
        <param field="Mode1" label="Device Topic" width="300px" default="sonoff"/>
        <param field="Mode2" label="Device Type" width="300px">
            <options>
                <option label="RGB" value="RGB" default="true"/>
                <option label="RGBW" value="RGBW"/>
                <option label="RGBWW" value="RGBWW"/>
                <option label="Dimmer (5x)" value="Dimmer" />
                <option label="Dimmer (5x) with Option68" value="PwmDimmer" />
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
from devices_manager import DevicesManager
from controllers.dimmer import Dimmer
from controllers.color_dimmer import ColorDimmer
from controllers.pwm_dimmer import PwmDimmer


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

        self.devices_manager = DevicesManager()
        self.devices_manager.set_devices(Devices)
        device_topic = Parameters["Mode1"].strip()

        if (Parameters["Mode2"] == "Dimmer"):
            self.controller = Dimmer(self.devices_manager, device_topic)
        elif (Parameters["Mode2"] == "PwmDimmer"):
            self.controller = PwmDimmer(self.devices_manager, device_topic)
        elif (Parameters["Mode2"] == "RGB"):
            self.controller = ColorDimmer(self.devices_manager, device_topic, 3)
        elif (Parameters["Mode2"] == "RGBW"):
            self.controller = ColorDimmer(self.devices_manager, device_topic, 4)
        elif (Parameters["Mode2"] == "RGBWW"):
            self.controller = ColorDimmer(self.devices_manager, device_topic, 5)

        self.controller.checkDevices()

        self.topics = list(["stat/" + device_topic + "/RESULT", "tele/" + device_topic + "/STATE"])
        
        mqtt_server_address = Parameters["Address"].strip()
        mqtt_server_port = Parameters["Port"].strip()
        mqtt_client_id = Parameters["Mode3"].strip()
        self.mqttClient = MqttClient(mqtt_server_address, mqtt_server_port, mqtt_client_id, self.onMQTTConnected, self.onMQTTDisconnected, self.onMQTTPublish, self.onMQTTSubscribed)

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
        self.mqttClient.onHeartbeat()

    def onMQTTConnected(self):
        Domoticz.Debug("onMQTTConnected")
        self.mqttClient.subscribe(self.topics)

    def onMQTTDisconnected(self):
        Domoticz.Debug("onMQTTDisconnected")

    def onMQTTSubscribed(self):
        Domoticz.Debug("onMQTTSubscribed")

    def onMQTTPublish(self, topic, message):
        Domoticz.Debug("MQTT message: " + topic + " " + str(message))

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