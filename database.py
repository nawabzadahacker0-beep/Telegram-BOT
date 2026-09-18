import json
import os
from datetime import datetime

class DeviceDatabase:
    def __init__(self):
        self.db_file = 'devices.json'
        self.load_devices()

    def load_devices(self):
        if os.path.exists(self.db_file):
            with open(self.db_file, 'r') as f:
                self.devices = json.load(f)
        else:
            self.devices = {}

    def save_devices(self):
        with open(self.db_file, 'w') as f:
            json.dump(self.devices, f)

    def get_device(self, device_id):
        return self.devices.get(device_id)

    def get_devices(self, chat_id):
        return [d for d in self.devices.values() if d.get('owner_id') == chat_id]

    def update_device(self, data):
        device_id = data.get('device_id')
        if device_id:
            self.devices[device_id] = {
                **self.devices.get(device_id, {}),
                **data,
                'last_seen': datetime.now().isoformat()
            }
            self.save_devices()
            return True
        return False

    def add_device(self, device_id, owner_id, name, model, android_version):
        self.devices[device_id] = {
            'device_id': device_id,
            'owner_id': owner_id,
            'name': name,
            'model': model,
            'android_version': android_version,
            'last_seen': datetime.now().isoformat()
        }
        self.save_devices()
        return True

    def remove_device(self, device_id):
        if device_id in self.devices:
            del self.devices[device_id]
            self.save_devices()
            return True
        return False
