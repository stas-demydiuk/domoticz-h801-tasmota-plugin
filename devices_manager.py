import Domoticz

class DevicesManager(object):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(DevicesManager, cls).__new__(cls)

        return cls.instance

    def set_devices(self, devices):
        self.devices = devices

    def get_device_by_unit(self, unit):
        return self.devices[unit]

    def has_device(self, unit):
        return unit in self.devices

    def create_device(self, name, unit, type, sub_type, switch_type):
        Domoticz.Device(Name=name, Unit=unit, Type=type, Subtype=sub_type, Switchtype=switch_type).Create()