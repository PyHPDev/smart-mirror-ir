import json
import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional

try:
    from .config import load_mirror_cache, save_mirror_cache, ensure_dirs
except ImportError:
    from config import load_mirror_cache, save_mirror_cache, ensure_dirs


def get_mirrors(country: str = "Iran") -> List[Dict]:
    base_path = os.path.dirname(__file__)
    if country.lower() == "iran":
        path = os.path.join(base_path, "data", "mirrors_ir.json")
    else:
        path = os.path.join(base_path, "data", "mirrors_cn.json")
    
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def is_valid_mirror(mirror: Dict, distro: str, codename: str) -> bool:
    url = mirror.get("url", "")
    if not url:
        return False
    
    # Try common paths
    test_paths = [
        f"{url}/{distro}/dists/{codename}/InRelease",
        f"{url}/debian/dists/{codename}/InRelease",
        f"{url}/ubuntu/dists/{codename}/InRelease",
    ]
    
    for test_url in test_paths:
        try:
            r = requests.head(test_url, timeout=8, allow_redirects=True)
            if r.status_code == 200:
                return True
        except:
            continue
    return False


def benchmark_mirrors_parallel(mirrors: List[Dict], distro: str, codename: str, max_workers: int = 8) -> List[Dict]:
    results = []
    
    def test_one(mirror):
        url = mirror.get("url", "")
        if not url:
            return None
        
        latency = None
        speed = 0
        
        # Latency test
        try:
            import time
            start = time.time()
            r = requests.head(f"{url}/{distro}/dists/{codename}/InRelease", timeout=6, allow_redirects=True)
            latency = round(time.time() - start, 3)
            if r.status_code != 200:
                return None
        except:
            return None
        
        # Simple speed test (download small file)
        try:
            start = time.time()
            r = requests.get(f"{url}/{distro}/dists/{codename}/Release", timeout=10, stream=True)
            if r.status_code == 200:
                downloaded = 0
                for chunk in r.iter_content(8192):
                    downloaded += len(chunk)
                    if downloaded > 50000:
                        break
                speed = int(downloaded / (time.time() - start) / 1024)
        except:
            speed = 50  # fallback
        
        score = (1000 / (latency + 0.1)) + (speed / 10)
        return {
            "name": mirror.get("name", url),
            "url": url,
            "latency": latency,
            "speed_kbps": speed,
            "score": round(score, 1)
        }
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_mirror = {executor.submit(test_one, m): m for m in mirrors}
        for future in as_completed(future_to_mirror):
            try:
                res = future.result()
                if res:
                    results.append(res)
            except Exception:
                pass
    
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def get_best_mirrors(country: str, distro: str, codename: str, force_refresh: bool = False) -> List[Dict]:
    cache = None if force_refresh else load_mirror_cache()
    if cache and cache.get("country") == country and cache.get("distro") == distro:
        return cache.get("results", [])
    
    mirrors = get_mirrors(country)
    valid = [m for m in mirrors if is_valid_mirror(m, distro, codename)]
    
    if not valid:
        valid = mirrors  # fallback
    
    results = benchmark_mirrors_parallel(valid, distro, codename)
    save_mirror_cache(results, country, distro)
    return results


def generate_apt_sources(mirrors: List[Dict], distro: str, codename: str) -> str:
    content = "# Smart Mirror IR - Optimized sources\n"
    content += f"# Generated for {distro} {codename}\n\n"
    
    # Determine correct components based on distro
    if distro.lower() == "ubuntu":
        components = "main restricted universe multiverse"
    else:
        # Debian and derivatives
        components = "main contrib non-free non-free-firmware"
    
    for m in mirrors:
        url = m["url"].rstrip("/")
        # Clean common wrong suffixes
        if url.endswith("/debian") or url.endswith("/ubuntu"):
            url = url.rsplit("/", 1)[0]
        
        content += f"deb {url}/{distro}/ {codename} {components}\n"
        content += f"deb {url}/{distro}/ {codename}-updates {components}\n"
        if "security" in url or "debian" in url.lower():
            content += f"deb {url}/{distro}-security {codename}-security {components}\n"
        content += "\n"
    
    return content


def generate_pacman_mirrorlist(mirrors: List[Dict]) -> str:
    content = "# Smart Mirror IR - Optimized Arch mirrors\n"
    for m in mirrors:
        content += f"Server = {m['url']}/archlinux/$repo/os/$arch\n"
    return content
