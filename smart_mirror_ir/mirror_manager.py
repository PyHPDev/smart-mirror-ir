import json
import os
from typing import List, Dict, Optional

import requests

from .validators import benchmark_mirrors_parallel, get_distro_path

from .config import load_mirror_cache, save_mirror_cache


def load_mirrors(country: str) -> List[Dict]:
    """Load curated mirrors for country."""
    base_dir = os.path.dirname(__file__)
    if country.lower() in ["iran", "ir"]:
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
    valid_results = benchmark_mirrors_parallel(mirrors, distro, codename)
    
    if not valid_results:
        raise RuntimeError("No working mirrors found for this distro/country! All tested mirrors failed validation.")
    
    top = valid_results[:10]
    save_mirror_cache(top, country, distro)
    return top


def generate_apt_sources(mirrors: List[Dict], distro: str, codename: str) -> str:
    """Generate professional sources.list for apt with full modern components."""
    lines = ["# Smart Mirror IR - Auto-generated - Do NOT edit manually"]
    lines.append(f"# Country: Iran/China | Distro: {distro} | Suite: {codename}")
    lines.append("# Generated with validation and speed benchmarking")
    lines.append("")
    
    components = "main contrib non-free non-free-firmware"
    
    for m in mirrors:
        base = m["url"].rstrip("/")
        path = get_distro_path(distro, m)
        proto = "https" if m.get("https_available", False) else "http"
        clean_base = base.replace("http://", "").replace("https://", "")
        url = f"{proto}://{clean_base}{path}"
        
        lines.append(f"deb {url} {codename} {components}")
        lines.append(f"deb {url} {codename}-updates {components}")
        lines.append(f"deb {url} {codename}-security {components}")
        lines.append("")
    
    return "\n".join(lines)


def generate_pacman_mirrorlist(mirrors: List[Dict], distro: str = "arch") -> str:
    """Generate mirrorlist for pacman (Arch)."""
    lines = ["# Smart Mirror IR - Best mirrors for Arch Linux"]
    lines.append("# Sorted by current speed and reliability")
    lines.append("# Generated automatically - validation passed")
    lines.append("")
    
    for m in mirrors:
        base = m["url"].rstrip("/")
        path = get_distro_path(distro, m)
        proto = "https" if m.get("https_available", False) else "http"
        clean_base = base.replace("http://", "").replace("https://", "")
        url = f"{proto}://{clean_base}{path}"
        lines.append(f"Server = {url}$repo/os/$arch")
    
    return "\n".join(lines)
