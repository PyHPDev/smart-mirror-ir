#!/bin/bash
#
# Smart Mirror IR - Professional Installer
# Handles sudo correctly for WSL and multi-user systems
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

# Determine the real user (even if run with sudo)
if [ -n "$SUDO_USER" ]; then
    REAL_USER="$SUDO_USER"
    REAL_HOME=$(eval echo ~$SUDO_USER)
else
    REAL_USER="$USER"
    REAL_HOME="$HOME"
fi

if [ "$EUID" -ne 0 ]; then
    error "This script needs root privileges for system configuration."
    error "Please run: sudo bash install.sh"
    exit 1
fi

log "Smart Mirror IR Professional Installation"

echo ""
cat << 'BANNER'
  _____                      _    __  __ _                     _____ _____
 / ____|                    | |  |  \/  (_)                   |_   _|  __ \
| (___  _ __ ___   __ _ _ __| |_ | \  / |_ _ __ _ __ ___  _ __  | | | |__) |
 \___ \| '_ ` _ \ / _` | '__| __|| |\/| | | '__| '__/ _ \| '__| | | |  _  /
 ____) | | | | | | (_| | |  | |_ | |  | | | |  | | | (_) | |    _| |_| | \ \
|_____/|_| |_| |_|[0m__,_|_|   \__||_|  |_|_|_|  |_|  \___/|_|   |_____|_|  \_\
BANNER
echo ""

log "Installing minimal packages..."
apt-get update -qq
apt-get install -y python3 python3-pip pipx curl --no-install-recommends 2>/dev/null || true

# Switch to the real user for pipx installation
log "Installing Smart Mirror IR for user '$REAL_USER' using pipx..."

if [ -n "$SUDO_USER" ]; then
    # Run pipx as the real user
    sudo -u "$SUDO_USER" pipx install . --force 2>/dev/null || \
    sudo -u "$SUDO_USER" pipx install git+https://github.com/PyHPDev/smart-mirror-ir.git --force
    
    sudo -u "$SUDO_USER" pipx ensurepath --quiet 2>/dev/null || true
else
    pipx install . --force 2>/dev/null || pipx install git+https://github.com/PyHPDev/smart-mirror-ir.git --force
    pipx ensurepath --quiet 2>/dev/null || true
fi

export PATH="$REAL_HOME/.local/bin:$PATH"

success "Installation completed successfully!"

echo ""
echo -e "${YELLOW}IMPORTANT - Run this command (or restart your terminal):${NC}"
echo "    source ~/.bashrc"
echo ""
echo -e "${GREEN}Then test:${NC}"
echo "    smart-mirror-ir --help"
echo "    smart-mirror-ir status"
echo ""
echo "After setup, normal commands like 'sudo apt install htop' will use smart mirrors."
