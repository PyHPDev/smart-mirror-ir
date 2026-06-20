"""Professional CLI for Smart Mirror IR using Rich for beautiful output."""

import argparse
import subprocess
import sys
import tempfile
import os
import shutil
from typing import List, Optional

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.progress import Progress, SpinnerColumn, TextColumn
    RICH = True
except ImportError:
    RICH = False
    Console = None


from .detector import detect_distro, confirm_or_edit_distro

from .mirror_manager import (
    get_best_mirrors, 
    generate_apt_sources, 
    generate_pacman_mirrorlist,
)
from .config import backup_file, get_sources_list_path, ensure_dirs

from .utils import (
    setup_logging, 
    print_success, 
    print_error, 
    print_warning, 
    print_info,
    get_logger
)

console = Console() if RICH else None
logger = get_logger()


def setup_wizard():
    """Interactive first-time setup wizard."""
    if RICH:
        console.print(Panel.fit(
            "[bold cyan]Smart Mirror IR Setup Wizard[/bold cyan]\n"
            "Intelligent mirror configuration for Iran & China", 
            border_style="cyan"
        ))
    else:
        print("=== Smart Mirror IR Setup Wizard ===")
    
    # Detect
    info = detect_distro()
    info = confirm_or_edit_distro(info)
    
    # Country selection
    if RICH:
        country = Prompt.ask(
            "Which country are you in? (this will be saved)", 
            choices=["Iran", "China"], 
            default="Iran"
        )
    else:
        country = input("Country (Iran/China) [Iran]: ").strip().capitalize() or "Iran"
    
    distro = info["distro"]
    codename = info.get("codename", "stable")
    pm = info["package_manager"]
    
    print_info(f"Starting mirror validation for {country} / {distro} ({codename})...")
    
    best_mirrors = []
    try:
        if RICH:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                task = progress.add_task("Benchmarking and validating mirrors...", total=None)
                best_mirrors = get_best_mirrors(country, distro, codename, force_refresh=True)
        else:
            print_info("Benchmarking mirrors (this may take 20-60 seconds)...")
            best_mirrors = get_best_mirrors(country, distro, codename, force_refresh=True)
    except Exception as e:
        print_error(f"Mirror benchmark failed: {str(e)}")
        print_error("Ready brother, this error in total! Check your internet connection or try again later.")
        sys.exit(1)
    
    # Show results nicely
    if RICH and best_mirrors:
        table = Table(title="Top Validated Mirrors (sorted by speed & reliability)")
        table.add_column("#", style="cyan", justify="right")
        table.add_column("Mirror Name", style="green")
        table.add_column("Latency (s)", style="yellow")
        table.add_column("Speed (KB/s)", style="magenta")
        table.add_column("Score", style="bold green")
        
        for i, m in enumerate(best_mirrors[: min(8, len(best_mirrors))], 1):
            table.add_row(
                str(i), 
                m.get("name", "Unknown"),
                str(m.get("latency", 0)),
                str(m.get("speed_kbps", 0)),
                str(m.get("score", 0))
            )
        console.print(table)
    elif best_mirrors:
        print("\nTop mirrors:")
        for i, m in enumerate(best_mirrors[:5], 1):
            print(f"  {i}. {m.get('name')} - {m.get('speed_kbps')} KB/s (score: {m.get('score')})")
    
    # Save chosen country for future use
    try:
        config_path = "/etc/smart-mirror-ir/config.yaml"
        import yaml
        os.makedirs("/etc/smart-mirror-ir", exist_ok=True)
        with open(config_path, "w") as f:
            yaml.dump({"country": country, "last_setup": "now"}, f)
    except:
        pass
    
    # Configure package manager
    ensure_dirs()
    sources_path = get_sources_list_path(pm)
    
    if pm == "apt":
        content = generate_apt_sources(best_mirrors[:5], distro, codename)
        backup = backup_file("/etc/apt/sources.list")
        if backup:
            print_info(f"Backed up original sources.list to {backup}")
        
        with open(sources_path, "w") as f:
            f.write(content)
        print_success(f"Created smart sources: {sources_path}")
        
        try:
            subprocess.run(["apt-get", "update", "-qq"], check=False, timeout=180)
        except Exception:
            pass
            
    elif pm == "pacman":
        content = generate_pacman_mirrorlist(best_mirrors[:6])
        backup_path = backup_file("/etc/pacman.d/mirrorlist")
        if backup_path:
            print_info(f"Backed up mirrorlist to {backup_path}")
        
        with open("/etc/pacman.d/mirrorlist", "w") as f:
            f.write(content)
        print_success("Updated /etc/pacman.d/mirrorlist with best mirrors")
        
        try:
            subprocess.run(["pacman", "-Sy"], check=False, timeout=90)
        except Exception:
            pass
    else:
        print_warning(f"Package manager '{pm}' detected. Smart sources created but you may need to configure manually.")
    
    print_success("Setup completed successfully! Your system now prefers fast local mirrors from " + country)
    print_info("Run 'smart-mirror-ir update-mirrors' anytime to refresh the list.")
    print_info("Use 'smart-mirror-ir install <package>' for smart installation with automatic fallback.")


def cmd_status():
    """Show current best mirrors status from cache."""
    print_info("Mirror status feature coming in next update. For now use 'update-mirrors'.")


def cmd_update_mirrors():
    """Force re-benchmark all mirrors."""
    info = detect_distro()
    
    # Try to load saved country
    country = "Iran"
    try:
        import yaml
        with open("/etc/smart-mirror-ir/config.yaml") as f:
            cfg = yaml.safe_load(f) or {}
            country = cfg.get("country", "Iran")
    except:
        pass
    
    if RICH:
        country = Prompt.ask("Country for benchmark", choices=["Iran", "China"], default=country)
    else:
        country = input(f"Country (Iran/China) [{country}]: ").strip().capitalize() or country
    
    print_info("Re-benchmarking mirrors... This may take 30-90 seconds. Please wait.")
    try:
        best = get_best_mirrors(country, info["distro"], info.get("codename", "stable"), force_refresh=True)
        print_success(f"Found {len(best)} working mirrors. Best: {best[0]['name']} @ {best[0]['speed_kbps']} KB/s")
    except Exception as e:
        print_error(str(e))
        print_error("Ready brother, this error in total! Please check your connection.")


def cmd_install(packages: List[str]):
    """Smart install using best mirrors with fallback."""
    if not packages:
        print_error("No packages specified. Example: smart-mirror-ir install htop vim")
        return
    
    info = detect_distro()
    pm = info["package_manager"]
    
    # Load saved country or detect
    country = "Iran"
    try:
        import yaml
        with open("/etc/smart-mirror-ir/config.yaml") as f:
            cfg = yaml.safe_load(f) or {}
            country = cfg.get("country", "Iran")
    except:
        if "ir" in info.get("id", "").lower():
            country = "Iran"
        else:
            country = "China"
    
    try:
        best_mirrors = get_best_mirrors(country, info["distro"], info.get("codename", "stable"))
    except Exception:
        best_mirrors = []
    
    if not best_mirrors:
        print_warning("No good mirrors cached. Running quick setup...")
        setup_wizard()
        return
    
    top_mirrors = best_mirrors[:5]
    
    if pm == "apt":
        content = generate_apt_sources(top_mirrors, info["distro"], info.get("codename", "stable"))
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".list", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        cmd = ["apt-get", "install", "-y", 
               "-o", f"Dir::Etc::SourceList={tmp_path}",
               "-o", "Dir::Etc::SourceParts=/dev/null",
               "-o", "Acquire::Retries=3"] + packages
        
        print_info(f"Installing {' '.join(packages)} using top smart mirrors from {country}...")
        try:
            subprocess.run(cmd, check=True, timeout=600)
            print_success("Installation completed successfully using smart mirrors!")
        except subprocess.CalledProcessError as e:
            print_error(f"Install failed (code {e.returncode})")
            print_error("Ready brother, this error in total! Try updating mirrors or check connection.")
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            
    elif pm == "pacman":
        backup = backup_file("/etc/pacman.d/mirrorlist")
        content = generate_pacman_mirrorlist(top_mirrors)
        with open("/etc/pacman.d/mirrorlist", "w") as f:
            f.write(content)
        
        print_info(f"Installing {' '.join(packages)} with smart mirrors...")
        try:
            subprocess.run(["pacman", "-S", "--noconfirm"] + packages, check=True, timeout=600)
            print_success("Installation successful!")
        except subprocess.CalledProcessError:
            print_error("Ready brother, this error in total!")
        finally:
            if backup and os.path.exists(backup):
                shutil.copy(backup, "/etc/pacman.d/mirrorlist")
    else:
        print_error(f"Package manager '{pm}' not fully supported yet. Please run 'smart-mirror-ir update-mirrors' first.")


def main():
    setup_logging()
    
    parser = argparse.ArgumentParser(
        description="Smart Mirror IR - Intelligent mirror system for Iran & China",
        epilog="Made with love for restricted networks. https://github.com/PyHPDev/smart-mirror-ir"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    p_setup = subparsers.add_parser("setup", help="Run interactive setup wizard (recommended first time)")
    p_setup.set_defaults(func=lambda args: setup_wizard())
    
    p_status = subparsers.add_parser("status", help="Show current mirror status")
    p_status.set_defaults(func=lambda args: cmd_status())
    
    p_update = subparsers.add_parser("update-mirrors", help="Force re-benchmark all mirrors")
    p_update.set_defaults(func=lambda args: cmd_update_mirrors())
    
    p_install = subparsers.add_parser("install", help="Smart install packages using best mirrors + fallback")
    p_install.add_argument("packages", nargs="+", help="Package names to install")
    p_install.set_defaults(func=lambda args: cmd_install(args.packages))
    
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
