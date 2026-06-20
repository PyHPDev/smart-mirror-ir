# Smart Mirror IR 🇮🇷 🇨🇳

**Professional, full-stack intelligent package mirror manager for Iran, China and restricted networks.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Linux-green.svg)

## English

Smart Mirror IR is a production-grade tool that automatically selects the fastest and most reliable package mirrors for Debian, Ubuntu, and Arch Linux (with support for others) in countries with internet restrictions like Iran and China.

### Key Features
- **Smart Benchmarking**: Parallel validation + real speed testing of mirrors
- **Automatic Configuration**: Updates sources.list / mirrorlist with top mirrors
- **pipx Support**: Clean, isolated installation
- **Systemd Integration**: Optional automatic daily mirror updates
- **Safe Operations**: Always creates backups before modifying system files
- **Multi-language README**: English + Persian + Chinese

### Quick Start (Recommended)

```bash
git clone https://github.com/PyHPDev/smart-mirror-ir.git
cd smart-mirror-ir
sudo bash install.sh
```

After installation, normal commands work:
```bash
sudo apt update && sudo apt install htop
smart-mirror-ir status
smart-mirror-ir update-mirrors
```

### Systemd Auto-Update (Professional)

```bash
sudo cp systemd/smart-mirror-ir.timer /etc/systemd/system/
sudo cp systemd/smart-mirror-ir.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now smart-mirror-ir.timer
```

## فارسی (پرشین)

**اسمارت میرور ای آر** یک ابزار حرفه‌ای و کامل برای مدیریت هوشمند میرورهای پکیج در ایران و چین است.

### ویژگی‌ها
- بنچمارک هوشمند و موازی
- پیکربندی خودکار منابع apt/pacman
- نصب تمیز با pipx
- پشتیبانی از systemd timer
- بکاپ خودکار قبل از هر تغییر

### شروع سریع
```bash
git clone https://github.com/PyHPDev/smart-mirror-ir.git
cd smart-mirror-ir
sudo bash install.sh
```

بعد از نصب، دستورات معمولی کار می‌کنند:
```bash
sudo apt update && sudo apt install htop
smart-mirror-ir status
```

## 中文 (Chinese)

**Smart Mirror IR** 是一个专业级别的工具，用于伊朗和中国等限制网络环境下自动选择最快、最可靠的软件包镜像。

### 主要特性
- 智能化镜像测速与验证
- 自动配置 apt/pacman 源
- 支持 pipx 清洁安装
- 支持 systemd 定时器自动更新

### 快速开始
```bash
git clone https://github.com/PyHPDev/smart-mirror-ir.git
cd smart-mirror-ir
sudo bash install.sh
```

---

**Made with care for the Iranian and Chinese Linux communities.**
