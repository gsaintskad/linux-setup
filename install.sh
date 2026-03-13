#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$HOME/.config"
BACKUP_DIR="$HOME/.config-backup-$(date +%Y%m%d-%H%M%S)"

echo "=== Linux Setup Installer ==="
echo "Source: $SCRIPT_DIR"
echo ""

# --- Install packages ---
install_packages() {
    echo "[1/3] Installing packages..."
    if command -v dnf &>/dev/null; then
        # Filter comments and empty lines from packages.txt
        grep -v '^#' "$SCRIPT_DIR/packages.txt" | grep -v '^$' | sudo dnf install -y --skip-unavailable $(cat)
    elif command -v pacman &>/dev/null; then
        echo "Arch detected — install packages manually from packages.txt"
        echo "Consider: yay -S \$(grep -v '^#' packages.txt | grep -v '^\$' | tr '\n' ' ')"
        return
    else
        echo "Unknown package manager. Install packages from packages.txt manually."
        return
    fi
    echo ""
}

# --- Backup existing configs ---
backup_configs() {
    echo "[2/3] Backing up existing configs to $BACKUP_DIR..."
    mkdir -p "$BACKUP_DIR"
    for dir in hypr waybar rofi kitty fastfetch; do
        if [ -d "$CONFIG_DIR/$dir" ]; then
            cp -r "$CONFIG_DIR/$dir" "$BACKUP_DIR/$dir"
            echo "  Backed up $dir"
        fi
    done
    echo ""
}

# --- Symlink configs ---
link_configs() {
    echo "[3/3] Linking configs..."
    for dir in hypr waybar rofi kitty fastfetch; do
        src="$SCRIPT_DIR/config/$dir"
        dest="$CONFIG_DIR/$dir"
        if [ -d "$src" ]; then
            mkdir -p "$dest"
            for file in "$src"/*; do
                fname="$(basename "$file")"
                # Remove existing file/link before symlinking
                rm -f "$dest/$fname"
                ln -s "$file" "$dest/$fname"
                echo "  $dest/$fname -> $file"
            done
        fi
    done

    # Wallpaper
    mkdir -p "$HOME/wallpapers"
    if [ -f "$SCRIPT_DIR/wallpapers/wallpaper.png" ]; then
        ln -sf "$SCRIPT_DIR/wallpapers/wallpaper.png" "$HOME/wallpapers/wallpaper.png"
        echo "  ~/wallpapers/wallpaper.png -> $SCRIPT_DIR/wallpapers/wallpaper.png"
    fi

    # Scripts
    mkdir -p "$HOME/.local/bin"
    for script in "$SCRIPT_DIR/scripts"/*.sh; do
        [ -f "$script" ] || continue
        fname="$(basename "$script")"
        ln -sf "$script" "$HOME/.local/bin/$fname"
        chmod +x "$script"
        echo "  ~/.local/bin/$fname -> $script"
    done

    echo ""
}

# --- Main ---
echo "This will:"
echo "  1. Install packages via dnf"
echo "  2. Backup existing configs"
echo "  3. Symlink new configs from this repo"
echo ""
read -rp "Continue? [y/N] " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

install_packages
backup_configs
link_configs

echo "=== Done! ==="
echo "Log out and back into Hyprland to apply changes."
echo "Your old configs are in: $BACKUP_DIR"
