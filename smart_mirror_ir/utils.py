import logging
import os
import sys
from datetime import datetime

try:
    from rich.logging import RichHandler
    from rich.console import Console
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

console = Console() if RICH_AVAILABLE else None


def get_log_file() -> str:
    """Return a writable log file path. Prefer /var/log if root, else user cache."""
    if os.geteuid() == 0:
        log_dir = "/var/log"
        log_file = os.path.join(log_dir, "smart-mirror-ir.log")
    else:
        log_dir = os.path.expanduser("~/.cache/smart-mirror-ir")
        log_file = os.path.join(log_dir, "smart-mirror-ir.log")
    
    try:
        os.makedirs(log_dir, exist_ok=True)
        # Test write permission
        with open(log_file, 'a', encoding='utf-8'):
            pass
        return log_file
    except (PermissionError, OSError):
        # Final fallback: /tmp
        return "/tmp/smart-mirror-ir.log"


def setup_logging(log_file: str = None):
    """Setup professional logging with fallback for permission issues."""
    if log_file is None:
        log_file = get_log_file()
    
    handlers = []
    
    # File handler (with fallback)
    try:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        handlers.append(file_handler)
    except Exception:
        pass  # ignore if still fails
    
    # Console handler with rich if available
    if RICH_AVAILABLE:
        console_handler = RichHandler(rich_tracebacks=True, console=console)
        console_handler.setLevel(logging.INFO)
    else:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('[%(levelname)s] %(message)s')
        console_handler.setFormatter(console_formatter)
    handlers.append(console_handler)
    
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=handlers,
        force=True
    )
    
    return logging.getLogger("smart_mirror_ir")


def get_logger(name: str = "smart_mirror_ir"):
    return logging.getLogger(name)


def print_success(msg: str):
    if RICH_AVAILABLE:
        console.print(f"[bold green]✓ {msg}[/bold green]")
    else:
        print(f"\033[92m✓ {msg}\033[0m")


def print_error(msg: str):
    if RICH_AVAILABLE:
        console.print(f"[bold red]✗ {msg}[/bold red]")
    else:
        print(f"\033[91m✗ {msg}\033[0m")


def print_warning(msg: str):
    if RICH_AVAILABLE:
        console.print(f"[bold yellow]⚠ {msg}[/bold yellow]")
    else:
        print(f"\033[93m⚠ {msg}\033[0m")


def print_info(msg: str):
    if RICH_AVAILABLE:
        console.print(f"[bold blue]ℹ {msg}[/bold blue]")
    else:
        print(f"\033[94mℹ {msg}\033[0m]")
