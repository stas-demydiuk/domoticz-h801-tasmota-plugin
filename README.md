# H801 LED WiFi Controller - Domoticz Python Plugin
Python plugin for Domoticz to control H801 LED WiFi Controller with Tasmota firmware via MQTT

## Prerequisites

1. Setup any MQTT server ([Mosquitto](https://mosquitto.org/) as example)
2. Flash your H801 controller with latest [Tasmota](https://github.com/arendst/Sonoff-Tasmota) firmware
- Enable MQTT support
- Set and remember `MQTT_TOPIC` in `user_config.h`

## Installation

1. Clone repository into your domoticz plugins folder
```
cd domoticz/plugins
git clone https://github.com/stas-demydiuk/domoticz-h801-tasmota-plugin.git h801-tasmota-plugin
```
2. Restart domoticz
3. Go to "Hardware" page and add new item with type "H801 LED WiFi Controller with Tasmota firmware"
4. Set your MQTT server address and port to plugin settings and previously selected `MQTT_TOPIC` as "Device Topic" param
5. Specify your module configuration. Currently supported configurations are:
- RGB Dimmer
- RGB + White Dimmer (RGBW)
- RGB + Cold White + Warm White Dimmer (RGBWW)
- 5x Independent Dimmers

Please note that this plugin needs the "updated" Plugin System which is currently only available in the beta-branch of Domoticz.
