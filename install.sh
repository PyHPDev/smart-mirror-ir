#!/bin/bash
#
# Smart Mirror IR - Professional Installer (pipx recommended)
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
    error "Run with sudo: sudo bash install.sh"
    exit 1
fi

log "Starting Smart Mirror IR installation (pipx recommended)..."

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

# Install dependencies
if command -v apt-get &> /dev/null; then
    apt-get update -qq
    apt-get install -y python3 python3-pip python3-venv pipx curl 2>/dev/null || true
elif command -v dnf &> /dev/null; then
    dnf install -y python3 python3-pip pipx curl 2>/dev/null || true
elif command -v pacman &> /dev/null; then
    pacman -Sy --noconfirm python python-pip curl 2>/dev/null || true
fi

# Try pipx first (recommended for CLI tools)
if command -v pipx &> /dev/null; then
    log "Using pipx for clean installation..."
    pipx install . --force 2>/dev/null || pipx install git+https://github.com/PyHPDev/smart-mirror-ir.git --force
    success "Installed via pipx. Command: smart-mirror-ir"
else
    log "pipx not found. Falling back to venv method..."
    # Fallback venv method (previous logic)
    INSTALL_DIR="/opt/smart-mirror-ir"
    VENV_DIR="$INSTALL_DIR/venv"
    mkdir -p "$INSTALL_DIR"
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip setuptools wheel -q
    pip install -e . -q
    
    WRAPPER="/usr/local/bin/smart-mirror-ir"
    cat > "$WRAPPER" << 'EOF'
#!/bin/bash
source /opt/smart-mirror-ir/venv/bin/activate
exec python -m smart_mirror_ir.cli "$@"
EOF
    chmod +x "$WRAPPER"
    success "Installed via venv fallback."
fi

log "Running initial setup wizard..."
python -m smart_mirror_ir.cli setup || true

success "Smart Mirror IR installed successfully!"
echo ""
echo -e "${GREEN}Usage:${NC}"
echo "  smart-mirror-ir --help"
echo "  smart-mirror-ir status"
echo "  sudo apt install htop          # Now uses smart Iranian mirrors automatically"
echo ""
echo -e "${YELLOW}For automatic updates, see systemd/ folder in the repo.${NC}"
