#!/bin/bash
#
# Smart Mirror IR - Clean Professional Installer
# Only installs what is absolutely necessary
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

if [ "$EUID" -ne 0 ]; then
    error "Run with sudo"
    exit 1
fi

log "Smart Mirror IR - Clean Installation"

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

# === ONLY minimal packages ===
log "Installing only required packages (python3 + pipx)..."
if command -v apt-get &> /dev/null; then
    apt-get update -qq
    apt-get install -y python3 python3-pip pipx curl --no-install-recommends 2>/dev/null || true
fi

if ! command -v pipx &> /dev/null; then
    error "pipx not found. Please install it manually."
    exit 1
fi

log "Installing Smart Mirror IR with pipx..."
pipx install . --force 2>/dev/null || pipx install git+https://github.com/PyHPDev/smart-mirror-ir.git --force

pipx ensurepath --quiet 2>/dev/null || true
export PATH="$HOME/.local/bin:$PATH"

success "Installation completed!"

echo ""
echo -e "${YELLOW}IMPORTANT:${NC} Run this command or restart your terminal:"
echo "    source ~/.bashrc"
echo ""
echo -e "${GREEN}Then test with:${NC}"
echo "    smart-mirror-ir --help"
echo "    smart-mirror-ir status"
echo ""
echo "Normal apt commands will now use smart Iranian mirrors."
