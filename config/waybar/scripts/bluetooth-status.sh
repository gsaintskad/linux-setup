#!/bin/bash
# Output bluetooth Nerd Font icon for waybar
# U+F00AF=bluetooth, U+F00B1=bluetooth-connected, U+F00B2=bluetooth-off
if bluetoothctl show | grep -q "Powered: yes"; then
    count=$(bluetoothctl devices Connected 2>/dev/null | grep -c "Device")
    if [ "$count" -gt 0 ]; then
        python3 -c "print(chr(0xF00B1), $count)"
    else
        python3 -c "print(chr(0xF00AF))"
    fi
else
    python3 -c "print(chr(0xF00B2))"
fi
