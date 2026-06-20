#!/bin/bash
#
# Smart Mirror IR - Professional Installer (pipx recommended)
# Clean, minimal, and robust for WSL / Ubuntu / Debian
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[SmartMirrorIR]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

if [ "$EUID" -ne 0 ]; then
    error "Please run with sudo: sudo bash install.sh"
    exit 1
fi

log "Starting Smart Mirror IR Professional Installation..."

echo ""
cat << 'EOF'
  _____                      _    __  __ _                     _____ _____
 / ____|                    | |  |  \/  (_)                   |_   _|  __ \
| (___  _ __ ___   __ _ _ __| |_ | \  / |_ _ __ _ __ ___  _ __  | | | |__) |
 \___ \| '_ ` _ \ / _` | '__| __|| |\/| | | '__| '__/ _ \| '__| | | |  _  /
 ____) | | | | | | (_| | |  | |_ | |  | | | |  | | | (_) | |    _| |_| | \ \
|_____/|_| |_| |_|[0m__,_|_|   \__||_|  |_|_|_|  |_|  \___/|_|   |_____|_|  \_\
EOF
echo ""

# === Minimal dependencies only ===
log "Installing minimal required packages..."
if command -v apt-get &> /dev/null; then
    apt-get update -qq
    apt-get install -y python3 python3-pip pipx curl 2>/dev/null || true
elif command -v dnf &> /dev/null; then
    dnf install -y python3 python3-pip pipx curl 2>/dev/null || true
elif command -v pacman &> /dev/null; then
    pacman -Sy --noconfirm python python-pip curl 2>/dev/null || true
fi

# Ensure pipx is in PATH
if command -v pipx &> /dev/null; then
    log "Using modern pipx installation..."
    
    # Install the package
    if [ -f "pyproject.toml" ]; then
        pipx install . --force --quiet 2>/dev/null || true
    else
        pipx install git+https://github.com/PyHPDev/smart-mirror-ir.git --force --quiet 2>/dev/null || true
    fi
    
    # Make sure pipx binaries are in PATH
    pipx ensurepath --quiet 2>/dev/null || true
    export PATH="$HOME/.local/bin:$PATH"
    
    success "Installed cleanly via pipx"
else
    error "pipx installation failed. Please install pipx manually and re-run."
    exit 1
fi

# Run setup wizard using the installed command
log "Running initial setup wizard..."
if command -v smart-mirror-ir &> /dev/null; then
    smart-mirror-ir setup || true
else
    # Fallback
    python3 -m smart_mirror_ir.cli setup 2>/dev/null || true
fi

success "Smart Mirror IR installed successfully!"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "  1. Restart your terminal or run: source ~/.bashrc"
echo "  2. Test with: smart-mirror-ir --help"
echo "  3. Check status: smart-mirror-ir status"
echo "  4. Normal commands now use smart mirrors: sudo apt install htop"
echo ""
echo -e "${YELLOW}For automatic daily updates, copy the systemd/ files.${NC}"
echo "Repository: https://github.com/PyHPDev/smart-mirror-ir"
