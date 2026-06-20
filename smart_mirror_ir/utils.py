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


def setup_logging(log_file: str = "/var/log/smart-mirror-ir.log"):
    """Setup professional logging."""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    handlers = []
    
    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    handlers.append(file_handler)
    
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
