# Linux Setup

Personal Hyprland + Fedora desktop config. One script to go from fresh install to full setup.

## What's Included

| Component | Config |
|---|---|
| **Hyprland** | Window manager (NVIDIA-ready, Catppuccin Mocha theme) |
| **Waybar** | Status bar |
| **Rofi** | App launcher + power menu |
| **Kitty** | Terminal emulator |
| **Fastfetch** | System info |
| **swww** | Wallpaper daemon |
| **hyprsunset** | Night light |

## System Requirements
- Fedora 43+ (or any systemd-based distro with Hyprland support)
- NVIDIA GPU (config includes NVIDIA Wayland env vars)
- Dual monitor setup (easily adjustable in hypr config)

## Quick Start
```bash
git clone <repo-url> ~/linux-setup
cd ~/linux-setup
chmod +x install.sh
./install.sh
```

## Structure
```
config/
  hypr/        # Hyprland compositor config
  waybar/      # Status bar config + styles
  rofi/        # Launcher config, themes, power menu
  kitty/       # Terminal config
  fastfetch/   # System info display
scripts/       # Helper scripts (keybinds cheatsheet, etc.)
wallpapers/    # Wallpaper collection
install.sh     # Main installer
packages.txt   # DNF packages to install
```
