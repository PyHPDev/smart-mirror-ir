import time
import urllib.request
import urllib.error
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Tuple, Optional, Dict

import requests


def get_distro_path(distro: str, mirror: dict) -> str:
    """Get the correct path prefix for a distro on this mirror. Prioritizes per-mirror overrides."""
    distro = distro.lower()
    if distro in ["ubuntu", "linuxmint", "pop_os"]:
        return mirror.get("ubuntu_path", "/ubuntu/")
    elif distro in ["debian", "kali", "trixie", "bookworm"]:
        return mirror.get("debian_path", "/debian/")
    elif distro == "arch":
        return mirror.get("arch_path", "/archlinux/")
    elif distro in ["fedora", "centos", "rocky", "alma"]:
        return mirror.get("fedora_path", "/fedora/")
    return "/"


def validate_and_benchmark(mirror: dict, distro: str, codename: str, timeout: int = 15) -> Optional[Dict]:
    """ 
    Professional validation + speed benchmark.
    Only real working mirrors with correct structure pass.
    """
    base = mirror["base_url"].rstrip("/")
    path = get_distro_path(distro, mirror)
    
    if distro.lower() in ["arch"]:
        test_url = urljoin(base + path, "core/os/x86_64/core.db")
    else:
        # Debian/Ubuntu style - use InRelease (small, signed, always present)
        test_url = urljoin(base + path, f"dists/{codename}/InRelease")
    
    start = time.time()
    try:
        headers = {"User-Agent": "SmartMirrorIR/1.0 (https://github.com/PyHPDev/smart-mirror-ir)"}
        
        # HEAD check
        resp = requests.head(test_url, timeout=timeout, headers=headers, allow_redirects=True)
        if resp.status_code != 200:
            return None
        
        latency = time.time() - start
        
        # Download small portion for real speed test
        download_start = time.time()
        downloaded = 0
        with requests.get(test_url, timeout=timeout, headers=headers, stream=True) as r:
            r.raise_for_status()
            for chunk in r.iter_content(chunk_size=8192):
                downloaded += len(chunk)
                if downloaded > 65536:
                    break
        download_time = max(time.time() - download_start, 0.001)
        speed_kbps = (downloaded / 1024) / download_time
        
        score = (1000 / (latency * 1000 + 1)) * (speed_kbps / 50 + 1)
        
        return {
            "name": mirror["name"],
            "url": base,
            "full_test_url": test_url,
            "latency": round(latency, 3),
            "speed_kbps": round(speed_kbps, 1),
            "score": round(score, 2),
            "status": "OK",
            "last_checked": time.time()
        }
    except Exception:
        return None


def benchmark_mirrors_parallel(mirrors: list, distro: str, codename: str, max_workers: int = 8) -> list:
    """Parallel benchmark. Only valid mirrors are returned, sorted by score."""
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_mirror = {executor.submit(validate_and_benchmark, m, distro, codename): m for m in mirrors}
        for future in as_completed(future_to_mirror):
            result = future.result()
            if result:
                results.append(result)
    results.sort(key=lambda x: x["score"], reverse=True)
    return results
