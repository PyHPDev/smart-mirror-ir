# Smart Mirror IR 🇮🇷🇨🇳

**Advanced Intelligent Package Mirror Management System for Iran, China, and countries with internet restrictions or slow official mirrors.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## عنوان فارسی

**اسمارت میرور ای آر** - سیستم هوشمند مدیریت میرورهای پکیج برای لینوکس

## Features (Advanced & Professional)

- **Smart Mirror Selection**: Automatically validates and benchmarks mirrors for speed and reliability.
- **Country Support**: Built-in optimized lists for **Iran (IR)** and **China (CN)** with 10+ high-quality mirrors each.
- **Multi-Distro Support**: Currently strong support for **Ubuntu/Debian (apt)** and **Arch Linux (pacman)**. Easy to extend for Fedora, openSUSE etc.
- **Professional Validation**:
  - HTTP status check
  - Content validation (correct Release/InRelease or core.db signature)
  - Real speed benchmark (download time + throughput)
  - Parallel testing with ThreadPoolExecutor for speed
- **Intelligent Fallback**: Ranks mirrors by performance. Uses top mirrors in package manager config for automatic failover.
- **Interactive Setup Wizard**: Detects your OS/distro/version, confirms with user, asks country, sets everything up.
- **CLI Tool**: `smart-mirror-ir` command after install.
  - `setup` / `reconfigure`
  - `update-mirrors` (re-benchmark all)
  - `status` (show current best mirrors with speeds)
  - `install <pkg>` (smart install using best mirrors - temp config + fallback)
- **Safe Configuration**: Always backups original sources/mirrorlist before modifying.
- **Caching**: Mirror status cached for 1 hour to avoid repeated slow tests.
- **Logging**: Detailed logs in `/var/log/smart-mirror-ir.log`
- **Systemd Ready**: Optional background service for periodic mirror health checks (future).
- **No Bugs Policy**: Clean code, proper error handling, type hints where possible, professional structure.

## Why Smart Mirror IR?

In countries like Iran and China, official global mirrors (archive.ubuntu.com, deb.debian.org, etc.) are often slow, blocked, or unreliable due to sanctions, Great Firewall, or routing issues.

This tool solves it by:
1. Maintaining curated lists of **local fast mirrors**.
2. Continuously validating which ones are alive and fast **right now**.
3. Automatically configuring your package manager to use the best ones **with failover**.
4. Providing a smart `install` command that tries the best mirrors in order.

## Requirements

- Linux (Ubuntu, Debian, Arch, Fedora, etc.)
- Python 3.8+
- sudo access for initial setup
- curl (usually pre-installed)

## Quick Start

```bash
git clone https://github.com/PyHPDev/smart-mirror-ir.git
cd smart-mirror-ir
sudo bash install.sh
```

During setup:
- It will detect your Linux distribution.
- Ask you to confirm or manually select (Iran / China).
- Validate and benchmark ~10-15 mirrors for your distro.
- Backup and configure your package sources/mirrorlist with the top fastest mirrors.
- Install the `smart-mirror-ir` CLI command.

After setup you can use:

```bash
smart-mirror-ir status
smart-mirror-ir update-mirrors
smart-mirror-ir install vim htop
```

## How the Smart Install Works

When you run `smart-mirror-ir install package1 package2`:

1. Loads the current best mirrors (from cache or quick recheck).
2. Creates a temporary sources.list / mirrorlist containing **only the top 5 best mirrors** for your distro (sorted by speed).
3. Runs the native package manager (`apt` or `pacman`) with this temporary config.
4. If the install succeeds → great!
5. If any mirror fails or package not found on first, it automatically has the next mirrors as fallback because multiple sources are listed.
6. If all fail (very rare) → shows friendly error: "Ready brother, all mirrors failed for this package. Check your internet or try VPN."

## Mirror Validation (Professional)

Every mirror is tested with:
- HEAD request to key files (InRelease for apt, core.db for pacman)
- If valid → download the file and measure:
  - Connection time
  - Total download time
  - Throughput (KB/s)
- Score = weighted (low latency + high speed)
- Invalid or timeout mirrors are discarded.

Only **real working mirrors** are used. No fake links.

## Adding New Mirrors or Distros

Edit `smart_mirror_ir/data/mirrors_ir.json` and `mirrors_cn.json`.
Each entry:
```json
{
  "name": "ArvanCloud",
  "base_url": "http://mirror.arvancloud.ir",
  "https": true,
  "notes": "Excellent for most distros"
}
```
Then implement validation logic in `validators.py` if new distro type.

## Project Structure

```
smart-mirror-ir/
├── README.md
├── install.sh
├── LICENSE
├── pyproject.toml
├── smart_mirror_ir/
│   ├── __init__.py
│   ├── cli.py
│   ├── core.py
│   ├── detector.py
│   ├── mirror_manager.py
│   ├── validators.py
│   ├── config.py
│   ├── utils.py
│   └── data/
│       ├── mirrors_ir.json
│       └── mirrors_cn.json
└── requirements.txt
```

## Roadmap / Future Features

- Full support for Fedora/dnf, openSUSE/zypper, Alpine/apk
- Systemd timer for automatic daily mirror refresh
- GUI (optional)
- Per-user vs system-wide config
- Integration with Flatpak/Snap/AppImage mirrors if needed
- Persian language interface option

## Contributing

Pull requests welcome! Especially for new mirror lists and distro support.

## License

MIT License. Free for personal and commercial use in Iran, China, and everywhere.

**Made with ❤️ for the Iranian and Chinese Linux community.**

If this tool helps you, please star the repo and share with friends!
