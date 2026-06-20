import os
import json
import shutil
from datetime import datetime
from typing import Dict, List, Optional

CACHE_DIR = "/var/cache/smart-mirror-ir"
CONFIG_DIR = "/etc/smart-mirror-ir"
BACKUP_DIR = os.path.join(CONFIG_DIR, "backups")


def ensure_dirs():
    os.makedirs(CACHE_DIR, exist_ok=True)
    os.makedirs(CONFIG_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)


def get_cache_path() -> str:
    return os.path.join(CACHE_DIR, "mirrors_status.json")


def load_mirror_cache() -> Optional[Dict]:
    path = get_cache_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Check if cache is fresh (< 1 hour)
            if datetime.now().timestamp() - data.get("timestamp", 0) < 3600:
                return data
        except:
            pass
    return None


def save_mirror_cache(results: List[Dict], country: str, distro: str):
    ensure_dirs()
    data = {
        "timestamp": datetime.now().timestamp(),
        "country": country,
        "distro": distro,
        "results": results
    }
    with open(get_cache_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def backup_file(original_path: str) -> str:
    ensure_dirs()
    if not os.path.exists(original_path):
        return ""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{os.path.basename(original_path)}.{timestamp}.bak"
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    shutil.copy2(original_path, backup_path)
    return backup_path


def get_sources_list_path(pm: str) -> str:
    if pm == "apt":
        return "/etc/apt/sources.list.d/smart-mirror-ir.list"
    elif pm == "pacman":
        return "/etc/pacman.d/mirrorlist.smart"
    return ""
