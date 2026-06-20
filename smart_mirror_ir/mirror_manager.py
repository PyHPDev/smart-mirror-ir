import json
import os
from typing import List, Dict, Optional

import requests

from .validators import benchmark_mirrors_parallel, get_distro_path

from .config import load_mirror_cache, save_mirror_cache


def load_mirrors(country: str) -> List[Dict]:
    """Load curated mirrors for country."""
    base_dir = os.path.dirname(__file__)
    if country.lower() == "iran" or country.lower() == "ir":
        path = os.path.join(base_dir, "data", "mirrors_ir.json")
    else:
        path = os.path.join(base_dir, "data", "mirrors_cn.json")
    
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_best_mirrors(country: str, distro: str, codename: str, force_refresh: bool = False) -> List[Dict]:
    """Get top validated mirrors. Uses cache if fresh."""
    cache = None if force_refresh else load_mirror_cache()
    
    if cache and cache.get("country") == country and cache.get("distro") == distro:
        return cache["results"]
    
    mirrors = load_mirrors(country)
    # Filter to those that support the distro (all do by default)
    valid_results = benchmark_mirrors_parallel(mirrors, distro, codename)
    
    if not valid_results:
        raise RuntimeError("No working mirrors found! All tested mirrors failed validation.")
    
    # Keep top 10 or all if less
    top = valid_results[:10]
    save_mirror_cache(top, country, distro)
    return top


def generate_apt_sources(mirrors: List[Dict], distro: str, codename: str) -> str:
    """Generate sources.list content for apt using top mirrors."""
    lines = ["# Smart Mirror IR - Generated automatically - Do not edit manually"]
    lines.append(f"# Country: IR/CN | Distro: {distro} | Generated for {codename}")
    lines.append("")
    
    for m in mirrors:
        base = m["url"].rstrip("/")
        path = get_distro_path(distro, m)  # reuse from validators
        # Use https if available
        proto = "https" if m.get("https_available", False) else "http"
        url = f"{proto}://{base.replace('http://','').replace('https://','')}{path}"
        lines.append(f"deb {url} {codename} main restricted universe multiverse")
        lines.append(f"deb {url} {codename}-updates main restricted universe multiverse")
        lines.append(f"deb {url} {codename}-security main restricted universe multiverse")
        lines.append("")
    
    return "\n".join(lines)


def generate_pacman_mirrorlist(mirrors: List[Dict], distro: str = "arch") -> str:
    """Generate mirrorlist for pacman."""
    lines = ["# Smart Mirror IR - Best mirrors for Arch Linux"]
    lines.append("# Sorted by current speed and reliability")
    lines.append("")
    
    for m in mirrors:
        base = m["url"].rstrip("/")
        path = get_distro_path(distro, m)
        proto = "https" if m.get("https_available", False) else "http"
        url = f"{proto}://{base.replace('http://','').replace('https://','')}{path}"
        lines.append(f"Server = {url}$repo/os/$arch")
    
    return "\n".join(lines)
