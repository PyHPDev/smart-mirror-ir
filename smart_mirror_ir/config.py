import os
import yaml
from typing import Dict, Any

CONFIG_PATH = "/etc/smart-mirror-ir/config.yaml"
DEFAULT_CONFIG = {
    "country": "Iran",
    "auto_update_interval_hours": 24,
    "max_mirrors_to_use": 5,
    "benchmark_timeout": 15,
    "enable_systemd_timer": False,
    "supported_distros": ["debian", "ubuntu", "arch"],
}

def load_config() -> Dict[str, Any]:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                user_config = yaml.safe_load(f) or {}
            config = DEFAULT_CONFIG.copy()
            config.update(user_config)
            return config
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(config: Dict[str, Any]):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

def get_config_value(key: str, default=None):
    config = load_config()
    return config.get(key, default)
