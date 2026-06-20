import time
import urllib.request
import urllib.error
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Tuple, Optional, Dict

import requests


def get_distro_path(distro: str, mirror: dict) -> str:
    """Get the correct path prefix for a distro on this mirror."""
    distro = distro.lower()
    if distro in ["ubuntu", "linuxmint", "pop_os"]:
        return mirror.get("ubuntu_path", "/ubuntu/")
    elif distro in ["debian", "kali"]:
        return mirror.get("debian_path", "/debian/")
    elif distro == "arch":
        return mirror.get("arch_path", "/archlinux/")
    elif distro in ["fedora", "centos", "rocky", "alma"]:
        return mirror.get("fedora_path", "/fedora/")
    return "/"


def validate_and_benchmark(mirror: dict, distro: str, codename: str, timeout: int = 12) -> Optional[Dict]:
    """ 
    Professional validation + speed benchmark for a mirror.
    Returns dict with status, latency, speed_kbps, score or None if invalid.
    """
    base = mirror["base_url"].rstrip("/")
    path = get_distro_path(distro, mirror)
    
    if distro.lower() == "arch":
        test_url = urljoin(base + path, "core/os/x86_64/core.db")
        # For arch, core.db is ~ few MB but we use HEAD first then small range if possible
        validate_url = test_url
    else:
        # Debian/Ubuntu style
        test_url = urljoin(base + path, f"dists/{codename}/InRelease")
        validate_url = test_url
    
    start = time.time()
    try:
        # First HEAD for quick check
        headers = {"User-Agent": "SmartMirrorIR/1.0 (https://github.com/PyHPDev/smart-mirror-ir)"}
        resp = requests.head(validate_url, timeout=timeout, headers=headers, allow_redirects=True)
        if resp.status_code != 200:
            return None
        
        latency = time.time() - start
        
        # Now download for real speed test (small file or first 64KB)
        download_start = time.time()
        with requests.get(validate_url, timeout=timeout, headers=headers, stream=True) as r:
            r.raise_for_status()
            downloaded = 0
            for chunk in r.iter_content(chunk_size=8192):
                downloaded += len(chunk)
                if downloaded > 65536:  # ~64KB is enough for benchmark
                    break
        download_time = time.time() - download_start
        
        if download_time < 0.001:
            download_time = 0.001
        speed_kbps = (downloaded / 1024) / download_time
        
        # Score: higher is better. Balance latency and speed
        # Lower latency + higher speed = better score
        score = (1000 / (latency * 1000 + 1)) * (speed_kbps / 50 + 1)
        
        return {
            "name": mirror["name"],
            "url": base,
            "full_test_url": validate_url,
            "latency": round(latency, 3),
            "speed_kbps": round(speed_kbps, 1),
            "score": round(score, 2),
            "status": "OK",
            "last_checked": time.time()
        }
    except (requests.exceptions.RequestException, urllib.error.URLError, Exception) as e:
        return None


def benchmark_mirrors_parallel(mirrors: list, distro: str, codename: str, max_workers: int = 8) -> list:
    """Benchmark all mirrors in parallel and return sorted list of valid ones."""
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_mirror = {
            executor.submit(validate_and_benchmark, m, distro, codename): m 
            for m in mirrors
        }
        for future in as_completed(future_to_mirror):
            result = future.result()
            if result:
                results.append(result)
    
    # Sort by score descending (best first)
    results.sort(key=lambda x: x["score"], reverse=True)
    return results
