"""Professional CLI for Smart Mirror IR using Rich for beautiful output."""

import argparse
import subprocess
import sys
import tempfile
import os
from typing import List

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
    load_mirrors
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
    
    # Country
    if RICH:
        country = Prompt.ask(
            "Which country are you in?", 
            choices=["Iran", "China"], 
            default="Iran"
        )
    else:
        country = input("Country (Iran/China): ").strip().capitalize() or "Iran"
    
    distro = info["distro"]
    codename = info["codename"]
    pm = info["package_manager"]
    
    print_info(f"Starting mirror validation for {country} / {distro} ({codename})...")
    
    try:
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) if RICH else None as progress:
            if RICH:
                task = progress.add_task("Benchmarking mirrors...", total=None)
            best_mirrors = get_best_mirrors(country, distro, codename, force_refresh=True)
    except Exception as e:
        print_error(f"Mirror benchmark failed: {e}")
        print_error("Ready brother, this error in total! Check your internet connection.")
        sys.exit(1)
    
    # Show results
    if RICH:
        table = Table(title="Top Validated Mirrors (sorted by speed)")
        table.add_column("Rank", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Latency (s)", style="yellow")
        table.add_column("Speed (KB/s)", style="magenta")
        table.add_column("Score", style="bold green")
        
        for i, m in enumerate(best_mirrors[:8], 1):
            table.add_row(
                str(i), 
                m["name"], 
                str(m["latency"]), 
                str(m["speed_kbps"]), 
                str(m["score"])
            )
        console.print(table)
    else:
        print("\nTop mirrors:")
        for i, m in enumerate(best_mirrors[:5], 1):
            print(f"  {i}. {m['name']} - {m['speed_kbps']} KB/s (score: {m['score']})")
    
    # Configure package manager
    ensure_dirs()
    sources_path = get_sources_list_path(pm)
    
    if pm == "apt":
        content = generate_apt_sources(best_mirrors[:5], distro, codename)
        backup = backup_file("/etc/apt/sources.list")
        if backup:
            print_info(f"Backed up original sources.list to {backup}")
        
        # Also backup sources.list.d if exists
        with open(sources_path, "w") as f:
            f.write(content)
        print_success(f"Created {sources_path} with top 5 mirrors")
        
        # Update
        try:
            subprocess.run(["apt-get", "update", "-qq"], check=False, timeout=120)
        except:
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
            subprocess.run(["pacman", "-Sy"], check=False, timeout=60)
        except:
            pass
    
    print_success("Setup completed! Your system now uses smart fast mirrors from " + country)
    print_info("You can run 'smart-mirror-ir update-mirrors' anytime to re-benchmark.")
    print_info("Use 'smart-mirror-ir install <package>' for smart installation with fallback.")


def cmd_status():
    """Show current best mirrors status."""
    # For simplicity, re-run a quick check or load cache
    print_info("Loading latest mirror status...")
    # In real use would load from cache or re-detect
    print_success("Use 'smart-mirror-ir update-mirrors' for fresh benchmark.")
    # TODO: implement full status from cache


def cmd_update_mirrors():
    """Force re-benchmark all mirrors."""
    info = detect_distro()
    country = Prompt.ask("Country", choices=["Iran", "China"], default="Iran") if RICH else input("Iran or China? ").strip()
    
    print_info("Re-benchmarking mirrors... This may take 30-60 seconds.")
    try:
        best = get_best_mirrors(country, info["distro"], info["codename"], force_refresh=True)
        print_success(f"Found {len(best)} working mirrors. Top: {best[0]['name']} @ {best[0]['speed_kbps']} KB/s")
    except Exception as e:
        print_error(str(e))
        print_error("Ready brother, this error in total!")


def cmd_install(packages: List[str]):
    """Smart install using best mirrors with fallback."""
    if not packages:
        print_error("No packages specified.")
        return
    
    info = detect_distro()
    pm = info["package_manager"]
    
    # Get best mirrors (from cache or quick)
    try:
        best_mirrors = get_best_mirrors("Iran" if "ir" in info.get("id","").lower() else "China", 
                                       info["distro"], info["codename"])
    except:
        best_mirrors = []
    
    if not best_mirrors:
        print_warning("No cached mirrors. Running quick setup first...")
        setup_wizard()
        return
    
    top_mirrors = best_mirrors[:5]
    
    if pm == "apt":
        sources_path = get_sources_list_path(pm)
        content = generate_apt_sources(top_mirrors, info["distro"], info["codename"])
        
        # Use temp file for this install
        with tempfile.NamedTemporaryFile(mode="w", suffix=".list", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        cmd = ["apt-get", "install", "-y", 
               "-o", f"Dir::Etc::SourceList={tmp_path}",
               "-o", "Dir::Etc::SourceParts=/dev/null",
               "-o", "Acquire::Retries=3"] + packages
        
        print_info(f"Installing {' '.join(packages)} using top smart mirrors...")
        try:
            result = subprocess.run(cmd, check=True, timeout=300)
            print_success("Installation completed successfully using smart mirrors!")
        except subprocess.CalledProcessError as e:
            print_error(f"Install failed with code {e.returncode}")
            print_error("Ready brother, this error in total! Try 'smart-mirror-ir update-mirrors' or check connection.")
        finally:
            os.unlink(tmp_path)
            
    elif pm == "pacman":
        # For pacman we temporarily replace mirrorlist
        backup = backup_file("/etc/pacman.d/mirrorlist")
        content = generate_pacman_mirrorlist(top_mirrors)
        with open("/etc/pacman.d/mirrorlist", "w") as f:
            f.write(content)
        
        print_info(f"Installing {' '.join(packages)} with smart mirrors...")
        try:
            result = subprocess.run(["pacman", "-S", "--noconfirm"] + packages, check=True, timeout=300)
            print_success("Installation successful!")
        except subprocess.CalledProcessError:
            print_error("Ready brother, this error in total!")
        finally:
            if backup:
                shutil.copy(backup, "/etc/pacman.d/mirrorlist")
    else:
        print_error(f"Package manager {pm} not fully supported yet. Use native command after running update-mirrors.")


def main():
    setup_logging()
    
    parser = argparse.ArgumentParser(
        description="Smart Mirror IR - Intelligent mirror system for Iran & China",
        epilog="Made with love for restricted networks. https://github.com/PyHPDev/smart-mirror-ir"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # setup
    p_setup = subparsers.add_parser("setup", help="Run interactive setup wizard")
    p_setup.set_defaults(func=lambda args: setup_wizard())
    
    # status
    p_status = subparsers.add_parser("status", help="Show current mirror status")
    p_status.set_defaults(func=lambda args: cmd_status())
    
    # update-mirrors
    p_update = subparsers.add_parser("update-mirrors", help="Force re-benchmark mirrors")
    p_update.set_defaults(func=lambda args: cmd_update_mirrors())
    
    # install
    p_install = subparsers.add_parser("install", help="Smart install packages using best mirrors")
    p_install.add_argument("packages", nargs="+", help="Packages to install")
    p_install.set_defaults(func=lambda args: cmd_install(args.packages))
    
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
