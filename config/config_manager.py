import json
import os
from typing import Dict, Any
from plexapi.server import PlexServer

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "plex": {
        "url": "",
        "token": "",
    },
    "processing": {
        "mode": "medium",
        "workers": {
            "light": 1,
            "medium": 2,
            "heavy": 4
        }
    },
    "libraries": [],
    "preserve_labels": ["overlays"],
    "initialized": False
}

class ConfigManager:
    def __init__(self):
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print("Error reading config file. Using default configuration.")
                return DEFAULT_CONFIG.copy()
        return DEFAULT_CONFIG.copy()

    def save_config(self) -> None:
        """Save current configuration to file"""
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)

    def get_worker_count(self) -> int:
        """Get number of workers based on processing mode"""
        mode = self.config["processing"]["mode"]
        return self.config["processing"]["workers"][mode]

    async def test_connection(self, url: str, token: str) -> bool:
        """Test Plex server connection"""
        try:
            PlexServer(url, token)
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False

    def needs_setup(self) -> bool:
        """Check if initial setup is needed"""
        return not self.config.get("initialized", False)

    def get_libraries(self) -> list:
        """Get configured libraries"""
        return self.config.get("libraries", [])

    def get_preserve_labels(self) -> list:
        """Get labels to preserve during cleanup"""
        return self.config.get("preserve_labels", ["overlays"])

    def update_config(self, key: str, value: Any) -> None:
        """Update a specific configuration value"""
        keys = key.split('.')
        current = self.config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value
        self.save_config()