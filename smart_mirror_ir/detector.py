import os
import platform
import subprocess
from typing import Dict, Optional


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
        "manjaro": "arch",  # treat as arch base
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


def confirm_or_edit_distro(info: Dict) -> Dict:
    """Interactive confirmation and editing of detected distro."""
    from rich.prompt import Prompt, Confirm
    from rich.console import Console
    
    console = Console()
    
    console.print("\n[bold cyan]System Detection Results:[/bold cyan]")
    console.print(f"  Distro ID : [green]{info.get('id', 'unknown')}[/green]")
    console.print(f"  Detected  : [green]{info.get('distro', 'unknown')}[/green] {info.get('pretty', '')}")
    console.print(f"  Codename  : [green]{info.get('codename', 'unknown')}[/green]")
    console.print(f"  Version   : [green]{info.get('version', 'unknown')}[/green]")
    console.print(f"  Package Manager: [green]{info.get('package_manager', 'unknown')}[/green]")
    
    if not Confirm.ask("\nIs this correct?", default=True):
        console.print("[yellow]Please enter correct values:[/yellow]")
        info["distro"] = Prompt.ask("Distro (ubuntu/debian/arch/fedora/...)", default=info["distro"]).lower()
        info["codename"] = Prompt.ask("Codename (jammy/noble/bookworm/...)", default=info["codename"]).lower()
        info["package_manager"] = Prompt.ask("Package Manager (apt/pacman/dnf)", default=info["package_manager"]).lower()
    
    return info
