# Linux Setup

Personal Hyprland + Fedora desktop config with custom GTK4 popups for volume/bluetooth management.

## What's Included

| Component | Description |
|---|---|
| **Hyprland** | Wayland compositor (NVIDIA-ready, Catppuccin Mocha theme) |
| **Waybar** | Status bar with interactive calendar, volume/bluetooth modules |
| **Rofi** | App launcher + power menu with Nerd Font icons |
| **Kitty** | Terminal emulator |
| **Volume popup** | GTK4/Libadwaita slider with device selector (click volume icon) |
| **Bluetooth popup** | GTK4/Libadwaita device manager with connect/forget (click BT icon) |
| **Keybinds viewer** | Auto-generated from hyprland.conf (Alt+C) |
| **swww** | Wallpaper daemon |
| **hyprsunset** | Night light (4000K) |

## System Requirements

- Fedora 43+ (tested) or any systemd-based distro with Hyprland support
- NVIDIA GPU (config includes NVIDIA Wayland env vars; remove if AMD/Intel)
- Python 3.10+ with GTK4 and Libadwaita bindings (for popups)

## Installation

### 1. Install Hyprland

```bash
sudo dnf install hyprland hyprland-devel xdg-desktop-portal-hyprland
```

### 2. Clone this repo

```bash
git clone https://github.com/gsaintskad/linux-setup.git ~/dev/linux-setup
cd ~/dev/linux-setup
```

### 3. Install dependencies

```bash
# Core packages
sudo dnf install waybar rofi-wayland kitty nautilus fastfetch swww hyprsunset hyprlock

# Screenshot tools
sudo dnf install grim slurp wl-clipboard

# Audio
sudo dnf install pavucontrol blueman

# GTK4 popup dependencies
sudo dnf install python3-gobject gtk4 libadwaita

# Fonts
sudo dnf install google-noto-fonts-common google-noto-sans-fonts
```

Install JetBrainsMono Nerd Font (required for all icons):

```bash
mkdir -p ~/.local/share/fonts
cd /tmp
curl -LO https://github.com/ryanoasis/nerd-fonts/releases/latest/download/JetBrainsMono.tar.xz
tar -xf JetBrainsMono.tar.xz -C ~/.local/share/fonts/
fc-cache -fv
```

### 4. Run the installer

```bash
chmod +x install.sh
./install.sh
```

This will:
- Back up your existing configs to `~/.config-backup-<timestamp>/`
- Symlink all configs from this repo into `~/.config/`
- Link helper scripts to `~/.local/bin/`

### 5. Set up keybinds viewer

```bash
mkdir -p ~/Documents/themes/keybinds
ln -sf ~/dev/linux-setup/scripts/keybinds.sh ~/Documents/themes/keybinds/keybinds.sh
ln -sf ~/dev/linux-setup/scripts/keybinds.rasi ~/Documents/themes/keybinds/keybinds.rasi
```

### 6. Configure monitors

Edit `~/.config/hypr/hyprland.conf` and adjust monitor lines to match your setup:

```
monitor=HDMI-A-2, 1920x1080@75, 0x0, 1
monitor=HDMI-A-3, 2560x1440@144, 1920x0, 1
```

Find your monitor names with `hyprctl monitors`.

### 7. Log out and select Hyprland

Log out of your current session, select **Hyprland** from the session picker on the login screen, and log in.

## Keybinds

| Key | Action |
|---|---|
| `Alt + Enter` | Terminal |
| `Alt + X` | App launcher |
| `Alt + Z` | Power menu |
| `Alt + Q` | Kill active window |
| `Alt + C` | Keybinds cheatsheet |
| `Alt + F` | Toggle floating |
| `Alt + S` | Toggle split |
| `Alt + F1` | Screenshot (area select) |
| `Super + Shift + S` | Screenshot (area select) |
| `Super + F` | Toggle fullscreen |
| `Super + E` | File manager |
| `Super + L` | Lock screen |
| `Super + K / J` | Kill / Start waybar |
| `Super + W/A/S/D` | Move focus |
| `Alt + 1-5` | Workspace 1-5 |
| `Ctrl + 1-5` | Workspace 6-10 |
| `Super + 1-5` | Move window to workspace 1-5 |

## Waybar Modules

- **Click volume icon** — GTK4 popup with slider and device selector
- **Click bluetooth icon** — GTK4 popup to connect/disconnect/forget devices
- **Hover clock** — Calendar popup (scroll to navigate, right-click to toggle month/year)
- **Click power icon** — Rofi power menu (shutdown, reboot, lock, suspend, logout)
- **Click Fedora icon** — App launcher

## Structure

```
config/
  hypr/hyprland.conf           # Compositor config + window rules
  waybar/config.jsonc           # Bar modules
  waybar/style.css              # Bar styling (Catppuccin Mocha)
  waybar/scripts/
    volume-popup.py             # GTK4 volume control popup
    bluetooth-popup.py          # GTK4 bluetooth manager popup
    bluetooth-status.sh         # Bluetooth icon status script
  rofi/                         # Launcher + power menu configs
  kitty/                        # Terminal config
  fastfetch/                    # System info config
scripts/
  keybinds.sh                   # Auto-parses hyprland.conf for keybind list
  keybinds.rasi                 # Rofi theme for keybinds viewer
wallpapers/
install.sh                      # Main installer
packages.txt                    # DNF package list
```

## Customization

- **Theme colors**: Catppuccin Mocha — edit `waybar/style.css` and `rofi/colors.rasi`
- **Wallpaper**: Replace `wallpapers/wallpaper.png` or change path in `hyprland.conf`
- **NVIDIA vars**: Remove the NVIDIA env block in `hyprland.conf` if using AMD/Intel GPU
- **Night light**: Adjust temperature in `hyprland.conf` (`hyprsunset --temperature 4000`)
