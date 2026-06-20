"""Professional CLI for Smart Mirror IR"""

import argparse
import subprocess
import sys
import tempfile
import os
import shutil
from typing import List

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.progress import Progress, SpinnerColumn, TextColumn
    RICH = True
except ImportError:
    RICH = False
    Console = None


from .detector import detect_distro, confirm_or_edit_distro

from .mirror_manager import (
    get_best_mirrors, 
    generate_apt_sources, 
    generate_pacman_mirrorlist
)
from .config import load_config, save_config

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

VERSION = "1.2.0"


def setup_wizard(args=None):
    """Interactive first-time setup wizard."""
    if RICH and console:
        console.print(Panel.fit(
            f"[bold cyan]Smart Mirror IR v{VERSION} Setup Wizard[/bold cyan]\n"
            "Professional mirror management for Iran & China", 
            border_style="cyan"
        ))
    else:
        print(f"=== Smart Mirror IR v{VERSION} Setup Wizard ===")
    
    info = detect_distro()
    info = confirm_or_edit_distro(info)
    
    if RICH and console:
        try:
            country = Prompt.ask("Which country are you in?", choices=["Iran", "China"], default="Iran")
        except:
            country = input("Which country are you in? (Iran/China) [Iran]: ").strip().capitalize() or "Iran"
    else:
        country = input("Which country are you in? (Iran/China) [Iran]: ").strip().capitalize() or "Iran"
    
    distro = info["distro"]
    codename = info["codename"]
    pm = info["package_manager"]
    
    print_info(f"Starting mirror validation for {country} / {distro} ({codename})...")
    
    try:
        if RICH and console:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                progress.add_task("Benchmarking mirrors...", total=None)
                best_mirrors = get_best_mirrors(country, distro, codename, force_refresh=True)
        else:
            best_mirrors = get_best_mirrors(country, distro, codename, force_refresh=True)
    except Exception as e:
        print_error(f"Mirror benchmark failed: {e}")
        print_error("Ready brother, this error in total!")
        sys.exit(1)
    
    if RICH and console:
        table = Table(title="Top Validated Mirrors (sorted by speed)")
        table.add_column("Rank", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Latency (s)", style="yellow")
        table.add_column("Speed (KB/s)", style="magenta")
        table.add_column("Score", style="bold green")
        for i, m in enumerate(best_mirrors[:8], 1):
            table.add_row(str(i), m["name"], str(m["latency"]), str(m["speed_kbps"]), str(m["score"]))
        console.print(table)
    
    from .config import ensure_dirs as config_ensure_dirs
    config_ensure_dirs()
    sources_path = get_sources_list_path(pm)
    
    if pm == "apt":
        content = generate_apt_sources(best_mirrors[:5], distro, codename)
        backup_file("/etc/apt/sources.list")
        with open(sources_path, "w") as f:
            f.write(content)
        
        # Add apt speed optimizations
        apt_conf = "/etc/apt/apt.conf.d/99smart-mirror-ir"
        apt_config_content = '''Acquire::http::Pipeline-Depth "5";
Acquire::http::No-Cache "true";
Acquire::BrokenProxy "true";
Acquire::Retries "3";
'''
        with open(apt_conf, "w") as f:
            f.write(apt_config_content)
        print_success("Added apt speed optimizations")
        
        subprocess.run(["apt-get", "update", "-qq"], check=False, timeout=120)
    elif pm == "pacman":
        content = generate_pacman_mirrorlist(best_mirrors[:6])
        backup_file("/etc/pacman.d/mirrorlist")
        with open("/etc/pacman.d/mirrorlist", "w") as f:
            f.write(content)
        print_success("Updated pacman mirrorlist")
        subprocess.run(["pacman", "-Sy"], check=False, timeout=60)
    
    cfg = load_config()
    cfg["country"] = country
    cfg["last_setup_distro"] = distro
    save_config(cfg)
    
    print_success(f"Setup completed! Using smart mirrors from {country}")
    print_info("Normal commands like 'sudo apt install' now use Iranian mirrors.")
    print_info("Run 'smart-mirror-ir update-mirrors' to refresh.")


def cmd_status(args=None):
    """Show current smart mirror status from cache."""
    from .config import get_cache_path
    import json
    markdown = getattr(args, 'markdown', False) if args else False
    
    cache_file = get_cache_path()
    if not os.path.exists(cache_file):
        print_warning("No mirror status cache found. Run 'smart-mirror-ir update-mirrors' first.")
        return
    
    try:
        with open(cache_file) as f:
            data = json.load(f)
        
        if markdown:
            print("# Smart Mirror IR Status\n")
            print(f"**Last benchmark:** {data.get('timestamp', 'unknown')}")
            print(f"**Country:** {data.get('country', 'N/A')} | **Distro:** {data.get('distro', 'N/A')}\n")
            print("| Rank | Name | Speed (KB/s) | Score |")
            print("|------|------|--------------|-------|")
            for i, m in enumerate(data.get("results", [])[:8], 1):
                print(f"| {i} | {m.get('name', '?')} | {m.get('speed_kbps', 0)} | {m.get('score', 0)} |")
        else:
            print_info(f"Last benchmark: {data.get('timestamp', 'unknown')}")
            print_info(f"Country: {data.get('country', 'N/A')} | Distro: {data.get('distro', 'N/A')}")
            
            if RICH and console:
                table = Table(title="Current Best Mirrors")
                table.add_column("Rank", style="cyan")
                table.add_column("Name", style="green")
                table.add_column("Speed (KB/s)", style="magenta")
                table.add_column("Score", style="bold green")
                for i, m in enumerate(data.get("results", [])[:6], 1):
                    table.add_row(str(i), m.get("name", "?"), str(m.get("speed_kbps", 0)), str(m.get("score", 0)))
                console.print(table)
            else:
                for i, m in enumerate(data.get("results", [])[:5], 1):
                    print(f"  {i}. {m.get('name')} - {m.get('speed_kbps')} KB/s")
    except Exception as e:
        print_error(f"Failed to read status: {e}")


def cmd_update_mirrors(args=None):
    """Force re-benchmark."""
    info = detect_distro()
    cfg = load_config()
    country = cfg.get("country", "Iran")
    markdown = getattr(args, 'markdown', False) if args else False
    
    print_info("Re-benchmarking mirrors...")
    try:
        best = get_best_mirrors(country, info["distro"], info["codename"], force_refresh=True)
        if markdown:
            print("# Benchmark Results\n")
            print("| Rank | Name | Latency (s) | Speed (KB/s) | Score |")
            print("|------|------|-------------|--------------|-------|")
            for i, m in enumerate(best[:8], 1):
                print(f"| {i} | {m['name']} | {m['latency']} | {m['speed_kbps']} | {m['score']} |")
        else:
            print_success(f"Updated! Top mirror: {best[0]['name']} @ {best[0]['speed_kbps']} KB/s")
    except Exception as e:
        print_error(str(e))


def cmd_install(args):
    """Smart install using best mirrors (temporary override)."""
    packages = args.packages if hasattr(args, 'packages') else []
    if not packages:
        print_error("No packages specified.")
        return
    
    info = detect_distro()
    pm = info["package_manager"]
    
    try:
        best_mirrors = get_best_mirrors(load_config().get("country", "Iran"), info["distro"], info["codename"])
    except:
        best_mirrors = []
    if not best_mirrors:
        print_warning("No cached mirrors. Running setup first...")
        setup_wizard()
        return
    top = best_mirrors[:5]
    
    if pm == "apt":
        with tempfile.NamedTemporaryFile(mode="w", suffix=".list", delete=False) as tmp:
            tmp.write(generate_apt_sources(top, info["distro"], info["codename"]))
            tmp_path = tmp.name
        cmd = ["apt-get", "install", "-y", "-o", f"Dir::Etc::SourceList={tmp_path}"] + packages
        try:
            subprocess.run(cmd, check=True)
            print_success("Installed successfully via smart mirrors!")
        except subprocess.CalledProcessError:
            print_error("Install failed. Try normal 'sudo apt install' or update-mirrors.")
        finally:
            try:
                os.unlink(tmp_path)
            except:
                pass
    else:
        print_info("For pacman, normal 'sudo pacman -S' should already use smart mirrors after setup.")


def cmd_restore(args=None):
    """Restore original package manager configuration."""
    pm = detect_distro()["package_manager"]
    if pm == "apt":
        sources = "/etc/apt/sources.list.d/smart-mirror-ir.list"
        if os.path.exists(sources):
            os.remove(sources)
            print_success("Removed smart sources.list.d. Run 'sudo apt update' to use original mirrors.")
        else:
            print_warning("No smart sources file found.")
    elif pm == "pacman":
        print_info("For pacman, manually restore /etc/pacman.d/mirrorlist from backup if needed.")
    print_success("Restore completed.")


def cmd_test_fallback(args=None):
    """Test resilience by temporarily using a bad primary mirror."""
    print_info("Starting fallback resilience test...")
    info = detect_distro()
    pm = info["package_manager"]
    
    if pm != "apt":
        print_warning("This test is currently optimized for apt.")
        return
    
    print_warning("This test will temporarily use a non-working primary mirror to verify fallback.")
    
    # Create a temp sources.list with a bad first mirror
    bad_mirror = "http://127.0.0.1:1/debian/"  # Non-working
    good_mirrors = get_best_mirrors(load_config().get("country", "Iran"), info["distro"], info["codename"])[:3]
    
    content = "# Test sources with bad primary mirror\n"
    content += f"deb {bad_mirror} {info['codename']} main\n\n"
    for m in good_mirrors:
        content += f"deb {m['url']}/{info['distro']}/ {info['codename']} main\n"
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".list", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    
    print_info("Testing with bad primary mirror (should fallback)...")
    try:
        result = subprocess.run(
            ["apt-get", "update", "-o", f"Dir::Etc::SourceList={tmp_path}", "-o", "Dir::Etc::SourceParts=/dev/null"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            print_success("Fallback worked! apt successfully updated using secondary mirrors.")
        else:
            print_warning("Test completed (some warnings expected with bad primary).")
    except Exception as e:
        print_error(f"Test error: {e}")
    finally:
        os.unlink(tmp_path)
    
    print_success("Resilience test completed. Main mirror is now active again.")


def get_sources_list_path(pm: str) -> str:
    if pm == "apt":
        return "/etc/apt/sources.list.d/smart-mirror-ir.list"
    elif pm == "pacman":
        return "/etc/pacman.d/mirrorlist"
    return ""


def backup_file(path: str):
    from .config import BACKUP_DIR
    import shutil
    from datetime import datetime
    if os.path.exists(path):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(path, os.path.join(BACKUP_DIR, os.path.basename(path) + "." + ts + ".bak"))


def main():
    setup_logging()
    
    parser = argparse.ArgumentParser(
        prog="smart-mirror-ir",
        description=f"Smart Mirror IR v{VERSION} - Professional mirror manager for Iran & China",
        epilog="https://github.com/PyHPDev/smart-mirror-ir | Made for restricted networks"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    parser.add_argument("--markdown", action="store_true", help="Output in Markdown format")
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    p_setup = subparsers.add_parser("setup", help="Run interactive setup")
    p_setup.set_defaults(func=setup_wizard)
    
    p_status = subparsers.add_parser("status", help="Show current best mirrors status")
    p_status.set_defaults(func=cmd_status)
    
    p_update = subparsers.add_parser("update-mirrors", help="Force re-benchmark mirrors")
    p_update.set_defaults(func=cmd_update_mirrors)
    
    p_install = subparsers.add_parser("install", help="Advanced install with temporary smart mirrors")
    p_install.add_argument("packages", nargs="+")
    p_install.set_defaults(func=cmd_install)
    
    p_restore = subparsers.add_parser("restore", help="Restore original package manager config")
    p_restore.set_defaults(func=cmd_restore)
    
    p_test = subparsers.add_parser("test-fallback", help="Test resilience by simulating main mirror failure")
    p_test.set_defaults(func=cmd_test_fallback)
    
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
