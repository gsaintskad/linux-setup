#!/bin/bash
# Auto-generate keybinds list from hyprland.conf and show in rofi

HYPR_CONF="$HOME/.config/hypr/hyprland.conf"
THEME="$HOME/Documents/themes/keybinds/keybinds.rasi"

trim() { local s="$1"; s="${s#"${s%%[![:space:]]*}"}"; s="${s%"${s##*[![:space:]]}"}"; echo "$s"; }

{
while IFS= read -r line; do
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    if [[ "$line" =~ ^bind(m)?[[:space:]]*=[[:space:]]*(.+) ]]; then
        is_mouse="${BASH_REMATCH[1]}"; rest="${BASH_REMATCH[2]}"
        IFS=',' read -r f1 f2 f3 f4 <<< "$rest"
        mod=$(trim "$f1"); key=$(trim "$f2"); action=$(trim "$f3"); args=$(trim "$f4")

        # Format mod + key
        mod="${mod//\$mainMod/Super}"; mod="${mod//ALT/Alt}"; mod="${mod//CTRL/Ctrl}"; mod="${mod//SHIFT/Shift}"; mod="${mod// / + }"
        key="${key//Return/Enter}"; key="${key//mouse:272/Left Mouse}"; key="${key//mouse:273/Right Mouse}"

        # Match description
        desc=""
        case "$action" in
            workspace) desc="Workspace $args" ;;
            movetoworkspace) desc="Move to WS $args" ;;
            killactive) desc="Kill active window" ;;
            exit) desc="Exit" ;;
            fullscreen) desc="Toggle fullscreen" ;;
            togglefloating) desc="Toggle floating" ;;
            togglesplit) desc="Toggle split" ;;
            movefocus) case "$args" in l) desc="Focus left";; r) desc="Focus right";; u) desc="Focus up";; d) desc="Focus down";; esac ;;
            movewindow) [[ -n "$is_mouse" ]] && desc="Move window" ;;
            resizewindow) [[ -n "$is_mouse" ]] && desc="Resize window" ;;
            exec)
                case "$args" in
                    *kitty*) desc="Terminal" ;;
                    *nautilus*) desc="File manager" ;;
                    *"rofi -show"*) desc="App launcher" ;;
                    *powermenu*) desc="Power menu" ;;
                    *keybinds*) desc="Keybinds" ;;
                    *swaylock*) desc="Lock screen" ;;
                    *"killall waybar"*) desc="Kill panel" ;;
                    *grim*) desc="Screenshot" ;;
                    *waybar) desc="Start panel" ;;
                    *volume-popup*) desc="Volume control" ;;
                    *bluetooth-popup*) desc="Bluetooth" ;;
                esac ;;
        esac
        [[ -z "$desc" ]] && continue
        printf "%-35s %s + %s\n" "$desc" "$mod" "$key"
    fi
done < "$HYPR_CONF"
} | rofi -dmenu -theme "$THEME" -p "Keybinds"
