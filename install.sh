#!/bin/bash
#
# Smart Mirror IR - Professional Installer
# For Iran, China and restricted networks
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[SmartMirrorIR]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

if [ "$EUID" -ne 0 ]; then
    error "This installer must be run as root (sudo bash install.sh)"
    exit 1
fi

log "Starting Smart Mirror IR installation..."

echo ""

# Safe banner using heredoc to avoid backtick command substitution issues
cat << 'BANNER'
  _____                      _    __  __ _                     _____ _____
 / ____|                    | |  |  \/  (_)                   |_   _|  __ \
| (___  _ __ ___   __ _ _ __| |_ | \  / |_ _ __ _ __ ___  _ __  | | | |__) |
 \___ \| '_ ` _ \ / _` | '__| __|| |\/| | | '__| '__/ _ \| '__| | | |  _  /
 ____) | | | | | | (_| | |  | |_ | |  | | | |  | | | (_) | |    _| |_| | \ \
|_____/|_| |_| |_|\__,_|_|   \__||_|  |_|_|_|  |_|  \___/|_|   |_____|_|  \_\
BANNER

echo ""

# Check Python3
if ! command -v python3 &> /dev/null; then
    log "Python3 not found. Installing..."
    if command -v apt-get &> /dev/null; then
        apt-get update -qq
        apt-get install -y python3 python3-pip python3-venv curl
    elif command -v dnf &> /dev/null; then
        dnf install -y python3 python3-pip python3-virtualenv curl
    elif command -v pacman &> /dev/null; then
        pacman -Sy --noconfirm python python-pip curl
    else
        error "Unsupported distro for automatic Python install. Please install Python 3.8+ manually."
        exit 1
    fi
    success "Python3 installed."
fi

PYTHON_VERSION=$(python3 -c 'import sys; print("%s.%s" % sys.version_info[:2])')
log "Detected Python $PYTHON_VERSION"

if python3 -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)"; then
    log "Python version OK."
else
    error "Python 3.8+ required. Please upgrade."
    exit 1
fi

# Create installation directory
INSTALL_DIR="/opt/smart-mirror-ir"
VENV_DIR="$INSTALL_DIR/venv"

log "Creating virtual environment in $VENV_DIR..."
mkdir -p "$INSTALL_DIR"
if [ -d "$VENV_DIR" ]; then
    rm -rf "$VENV_DIR"
fi
python3 -m venv "$VENV_DIR"

# Activate venv
source "$VENV_DIR/bin/activate"

log "Upgrading pip..."
pip install --upgrade pip setuptools wheel -q

log "Installing dependencies..."
pip install -r requirements.txt -q

log "Installing Smart Mirror IR package in editable mode..."
pip install -e . -q

# Create wrapper script for CLI
WRAPPER="/usr/local/bin/smart-mirror-ir"
log "Creating system command: $WRAPPER"

cat > "$WRAPPER" << 'EOF'
#!/bin/bash
source /opt/smart-mirror-ir/venv/bin/activate
exec python -m smart_mirror_ir.cli "$@"
EOF

chmod +x "$WRAPPER"

success "Installation completed successfully!"

echo ""
log "Running initial setup wizard..."
echo ""

# Run the interactive setup
deactivate 2>/dev/null || true
source "$VENV_DIR/bin/activate"
python -m smart_mirror_ir.cli setup

success "Smart Mirror IR is ready to use!"
echo ""
echo -e "${GREEN}Try these commands:${NC}"
echo "  smart-mirror-ir --help"
echo "  smart-mirror-ir status"
echo "  smart-mirror-ir install htop"
echo ""
echo -e "${YELLOW}Repository: https://github.com/PyHPDev/smart-mirror-ir${NC}"
echo "Made with love for Iran & China Linux users ❤️"
