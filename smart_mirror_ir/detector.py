import os
import platform
import subprocess
from typing import Dict, Optional

try:
    from rich.prompt import Prompt, Confirm
    from rich.console import Console
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Prompt = None
    Confirm = None
    Console = None


def detect_distro() -> Dict:
    """Detect Linux distribution professionally using /etc/os-release and fallbacks."""
    info = {
        "distro": "unknown",
        "codename": "unknown",
        "version": "unknown",
        "package_manager": "unknown",
        "id": "unknown"
    }
    
    os_release = "/etc/os-release"
    if os.path.exists(os_release):
        with open(os_release) as f:
            for line in f:
                if line.startswith("ID="):
                    info["id"] = line.split("=")[1].strip().strip('"').lower()
                elif line.startswith("VERSION_CODENAME="):
                    info["codename"] = line.split("=")[1].strip().strip('"').lower()
                elif line.startswith("VERSION_ID="):
                    info["version"] = line.split("=")[1].strip().strip('"')
                elif line.startswith("PRETTY_NAME="):
                    info["pretty"] = line.split("=")[1].strip().strip('"')
    
    # Map to common names
    distro_map = {
        "ubuntu": "ubuntu",
        "debian": "debian",
        "linuxmint": "linuxmint",
        "pop": "pop_os",
        "arch": "arch",
        "manjaro": "arch",
        "fedora": "fedora",
        "centos": "centos",
        "rocky": "rocky",
        "almalinux": "alma"
    }
    
    info["distro"] = distro_map.get(info["id"], info["id"])
    
    # Detect package manager
    if os.path.exists("/usr/bin/apt") or os.path.exists("/usr/bin/apt-get"):
        info["package_manager"] = "apt"
    elif os.path.exists("/usr/bin/pacman"):
        info["package_manager"] = "pacman"
    elif os.path.exists("/usr/bin/dnf"):
        info["package_manager"] = "dnf"
    elif os.path.exists("/usr/bin/yum"):
        info["package_manager"] = "yum"
    else:
        info["package_manager"] = "unknown"
    
    # Fallback codename for Ubuntu/Debian
    if info["codename"] == "unknown" and info["package_manager"] == "apt":
        try:
            result = subprocess.run(["lsb_release", "-cs"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                info["codename"] = result.stdout.strip().lower()
        except:
            pass
    
    return info


def _safe_confirm(message: str, default: bool = True) -> bool:
    """Safe confirm with fallback for encoding issues (WSL, non-UTF8 terminals)."""
    if RICH_AVAILABLE:
        try:
            return Confirm.ask(message, default=default)
        except (UnicodeDecodeError, Exception):
            pass  # fallback
    
    # Fallback to plain input
    default_str = "y" if default else "n"
    while True:
        try:
            ans = input(f"{message} [y/n] (default: {default_str}): ").strip().lower()
            if ans in ["y", "yes", ""]:
                return True
            if ans in ["n", "no"]:
                return False
        except (EOFError, KeyboardInterrupt):
            return default
    return default


def _safe_prompt(message: str, default: str = "") -> str:
    """Safe prompt with fallback."""
    if RICH_AVAILABLE:
        try:
            return Prompt.ask(message, default=default)
        except (UnicodeDecodeError, Exception):
            pass
    
    try:
        ans = input(f"{message} (default: {default}): ").strip()
        return ans if ans else default
    except (EOFError, KeyboardInterrupt):
        return default


def confirm_or_edit_distro(info: Dict) -> Dict:
    """Interactive confirmation and editing of detected distro."""
    console = Console() if RICH_AVAILABLE else None
    
    if console:
        console.print("\n[bold cyan]System Detection Results:[/bold cyan]")
        console.print(f"  Distro ID : [green]{info.get('id', 'unknown')}[/green]")
        console.print(f"  Detected  : [green]{info.get('distro', 'unknown')}[/green] {info.get('pretty', '')}")
        console.print(f"  Codename  : [green]{info.get('codename', 'unknown')}[/green]")
        console.print(f"  Version   : [green]{info.get('version', 'unknown')}[/green]")
        console.print(f"  Package Manager: [green]{info.get('package_manager', 'unknown')}[/green]")
    else:
        print("\nSystem Detection Results:")
        print(f"  Distro ID : {info.get('id', 'unknown')}")
        print(f"  Detected  : {info.get('distro', 'unknown')} {info.get('pretty', '')}")
        print(f"  Codename  : {info.get('codename', 'unknown')}")
        print(f"  Version   : {info.get('version', 'unknown')}")
        print(f"  Package Manager: {info.get('package_manager', 'unknown')}")
    
    if not _safe_confirm("\nIs this correct?", default=True):
        if console:
            console.print("[yellow]Please enter correct values:[/yellow]")
        else:
            print("Please enter correct values:")
        
        info["distro"] = _safe_prompt("Distro (ubuntu/debian/arch/fedora/...)", default=info["distro"]).lower()
        info["codename"] = _safe_prompt("Codename (jammy/noble/bookworm/trixie/...)", default=info["codename"]).lower()
        info["package_manager"] = _safe_prompt("Package Manager (apt/pacman/dnf)", default=info["package_manager"]).lower()
    
    return info
