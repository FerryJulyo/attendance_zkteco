import json
import os

class Config:
    def __init__(self):
        self.config_file = "config.json"
        self.default_config = {
            "outlet": "HP777",
            "machine_ip": "0.0.0.0",
            "machine_id": "1",
            "api_url": "https://eportal.happypuppy.id/Api/",
            "jwt_secret": "Kontil"
        }
        self.load_config()
    
    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    self.__dict__.update(loaded_config)
            except:
                self.__dict__.update(self.default_config)
        else:
            self.__dict__.update(self.default_config)
            self.save_config()
    
    def save_config(self):
        config_to_save = {key: value for key, value in self.__dict__.items() 
                         if key in self.default_config}
        with open(self.config_file, 'w') as f:
            json.dump(config_to_save, f, indent=4)
    
    def update_config(self, **kwargs):
        for key, value in kwargs.items():
            if key in self.default_config:
                setattr(self, key, value)
        self.save_config()