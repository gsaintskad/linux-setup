#!/usr/bin/env python3
"""Waybar Bluetooth popup — GTK4 + Libadwaita dropdown with device management."""

import subprocess
import sys
import threading
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Gdk", "4.0")
from gi.repository import Gtk, Adw, Gdk, GLib


def run(cmd, timeout=5):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except subprocess.TimeoutExpired:
        return ""


def bt_powered():
    out = run(["bluetoothctl", "show"])
    return "Powered: yes" in out


def bt_toggle_power():
    powered = bt_powered()
    run(["bluetoothctl", "power", "off" if powered else "on"])


def bt_get_paired():
    """Return list of (mac, name, connected, icon) for paired devices."""
    out = run(["bluetoothctl", "devices", "Paired"])
    devices = []
    for line in out.splitlines():
        # "Device EC:46:54:45:03:F0 AirPods Pro"
        parts = line.split(" ", 2)
        if len(parts) < 3:
            continue
        mac = parts[1]
        name = parts[2]
        info = run(["bluetoothctl", "info", mac])
        connected = "Connected: yes" in info
        icon = "audio-headphones"
        for info_line in info.splitlines():
            if "Icon:" in info_line:
                icon = info_line.split("Icon:")[1].strip()
                break
        devices.append((mac, name, connected, icon))
    return devices


def bt_connect(mac):
    run(["bluetoothctl", "connect", mac], timeout=10)


def bt_disconnect(mac):
    run(["bluetoothctl", "disconnect", mac], timeout=5)


def bt_scan_devices(callback):
    """Scan for new devices in background, call callback with results."""
    def _scan():
        # Start scan
        subprocess.Popen(
            ["bluetoothctl", "scan", "on"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        import time
        time.sleep(4)
        subprocess.Popen(
            ["bluetoothctl", "scan", "off"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # Get all devices (paired + discovered)
        out = run(["bluetoothctl", "devices"])
        paired_out = run(["bluetoothctl", "devices", "Paired"])
        paired_macs = set()
        for line in paired_out.splitlines():
            parts = line.split(" ", 2)
            if len(parts) >= 2:
                paired_macs.add(parts[1])

        new_devices = []
        for line in out.splitlines():
            parts = line.split(" ", 2)
            if len(parts) < 3:
                continue
            mac = parts[1]
            name = parts[2]
            if mac not in paired_macs and not name.startswith("Device "):
                new_devices.append((mac, name))
        GLib.idle_add(callback, new_devices)

    t = threading.Thread(target=_scan, daemon=True)
    t.start()


ICON_MAP = {
    "audio-headphones": "audio-headphones-symbolic",
    "audio-headset": "audio-headphones-symbolic",
    "audio-card": "audio-speakers-symbolic",
    "input-keyboard": "input-keyboard-symbolic",
    "input-mouse": "input-mouse-symbolic",
    "input-gaming": "input-gaming-symbolic",
    "input-tablet": "input-tablet-symbolic",
    "phone": "phone-symbolic",
    "computer": "computer-symbolic",
}


def get_icon_name(icon):
    return ICON_MAP.get(icon, "bluetooth-symbolic")


class BluetoothPopup(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.waybar.bluetooth-popup")
        self.connect("activate", self.on_activate)
        self._scanning = False
        self._close_timer = None

    def on_activate(self, app):
        self.win = Adw.ApplicationWindow(application=app)
        self.win.set_default_size(340, -1)
        self.win.set_resizable(False)
        self.win.set_title("Bluetooth")
        self.win.set_decorated(False)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.main_box.add_css_class("main-box")

        # Header
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header_box.set_margin_start(16)
        header_box.set_margin_end(8)
        header_box.set_margin_top(12)
        header_box.set_margin_bottom(4)

        title = Gtk.Label(label="Bluetooth")
        title.add_css_class("title-3")
        title.set_hexpand(True)
        title.set_halign(Gtk.Align.START)
        header_box.append(title)

        # Scan button
        self.scan_btn = Gtk.Button()
        self.scan_btn.set_icon_name("view-refresh-symbolic")
        self.scan_btn.add_css_class("flat")
        self.scan_btn.add_css_class("circular")
        self.scan_btn.set_tooltip_text("Scan for devices")
        self.scan_btn.connect("clicked", self.on_scan)
        header_box.append(self.scan_btn)

        # Settings button
        settings_btn = Gtk.Button()
        settings_btn.set_icon_name("emblem-system-symbolic")
        settings_btn.add_css_class("flat")
        settings_btn.add_css_class("circular")
        settings_btn.set_tooltip_text("Bluetooth Settings")
        settings_btn.connect("clicked", self.on_settings)
        header_box.append(settings_btn)

        self.main_box.append(header_box)

        # Power toggle row
        power_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        power_row.set_margin_start(16)
        power_row.set_margin_end(16)
        power_row.set_margin_top(4)
        power_row.set_margin_bottom(8)

        power_icon = Gtk.Image.new_from_icon_name("bluetooth-symbolic")
        power_row.append(power_icon)

        power_label = Gtk.Label(label="Bluetooth")
        power_label.set_hexpand(True)
        power_label.set_halign(Gtk.Align.START)
        power_row.append(power_label)

        self.power_switch = Gtk.Switch()
        self.power_switch.set_active(bt_powered())
        self.power_switch.connect("state-set", self.on_power_toggle)
        power_row.append(self.power_switch)

        self.main_box.append(power_row)
        self.main_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # Paired devices section
        self.paired_header = Gtk.Label(label="Paired Devices")
        self.paired_header.add_css_class("caption")
        self.paired_header.set_halign(Gtk.Align.START)
        self.paired_header.set_margin_start(16)
        self.paired_header.set_margin_top(8)
        self.paired_header.set_margin_bottom(4)
        self.paired_header.set_opacity(0.7)
        self.main_box.append(self.paired_header)

        self.device_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.device_box.set_margin_start(8)
        self.device_box.set_margin_end(8)
        self.device_box.set_margin_bottom(8)
        self.main_box.append(self.device_box)

        # Discovered devices section (hidden initially)
        self.discovered_sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.discovered_sep.set_visible(False)
        self.main_box.append(self.discovered_sep)

        self.discovered_header = Gtk.Label(label="Available Devices")
        self.discovered_header.add_css_class("caption")
        self.discovered_header.set_halign(Gtk.Align.START)
        self.discovered_header.set_margin_start(16)
        self.discovered_header.set_margin_top(8)
        self.discovered_header.set_margin_bottom(4)
        self.discovered_header.set_opacity(0.7)
        self.discovered_header.set_visible(False)
        self.main_box.append(self.discovered_header)

        self.discovered_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.discovered_box.set_margin_start(8)
        self.discovered_box.set_margin_end(8)
        self.discovered_box.set_margin_bottom(12)
        self.discovered_box.set_visible(False)
        self.main_box.append(self.discovered_box)

        # Scan spinner (hidden initially)
        self.spinner_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.spinner_box.set_halign(Gtk.Align.CENTER)
        self.spinner_box.set_margin_top(8)
        self.spinner_box.set_margin_bottom(12)
        self.spinner = Gtk.Spinner()
        self.spinner_box.append(self.spinner)
        self.spinner_label = Gtk.Label(label="Scanning...")
        self.spinner_label.add_css_class("caption")
        self.spinner_label.set_opacity(0.7)
        self.spinner_box.append(self.spinner_label)
        self.spinner_box.set_visible(False)
        self.main_box.append(self.spinner_box)

        self.populate_devices()

        # CSS
        css = Gtk.CssProvider()
        css.load_from_string("""
            .main-box {
                background-color: alpha(@window_bg_color, 0.95);
            }
            .device-btn {
                padding: 8px 12px;
                border-radius: 8px;
            }
            .device-btn.connected {
                background-color: alpha(@accent_color, 0.15);
            }
            .status-label {
                font-size: 0.8em;
            }
        """)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.win.set_content(self.main_box)

        # Focus loss with delay
        self.win.connect("notify::is-active", self.on_focus_changed)

        # Escape to close
        esc = Gtk.EventControllerKey()
        esc.connect("key-pressed", self.on_key)
        self.win.add_controller(esc)

        self.win.present()

    def populate_devices(self):
        while child := self.device_box.get_first_child():
            self.device_box.remove(child)

        if not bt_powered():
            label = Gtk.Label(label="Bluetooth is off")
            label.set_opacity(0.5)
            label.set_margin_top(8)
            label.set_margin_bottom(8)
            self.device_box.append(label)
            return

        devices = bt_get_paired()
        if not devices:
            label = Gtk.Label(label="No paired devices")
            label.set_opacity(0.5)
            label.set_margin_top(8)
            label.set_margin_bottom(8)
            self.device_box.append(label)
            return

        for mac, name, connected, icon in devices:
            btn = Gtk.Button()
            btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

            icon_widget = Gtk.Image.new_from_icon_name(get_icon_name(icon))
            btn_box.append(icon_widget)

            text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            text_box.set_hexpand(True)
            text_box.set_halign(Gtk.Align.START)

            name_label = Gtk.Label(label=name)
            name_label.set_halign(Gtk.Align.START)
            name_label.set_ellipsize(3)
            text_box.append(name_label)

            status = Gtk.Label(label="Connected" if connected else "Not connected")
            status.add_css_class("caption")
            status.add_css_class("status-label")
            status.set_halign(Gtk.Align.START)
            status.set_opacity(0.6)
            text_box.append(status)

            btn_box.append(text_box)

            if connected:
                disconnect_icon = Gtk.Image.new_from_icon_name("media-eject-symbolic")
                disconnect_icon.set_opacity(0.6)
                btn_box.append(disconnect_icon)
                btn.add_css_class("connected")

            btn.set_child(btn_box)
            btn.add_css_class("flat")
            btn.add_css_class("device-btn")
            btn.connect("clicked", self.on_device_clicked, mac, connected)

            # Right-click context menu
            gesture = Gtk.GestureClick(button=3)
            gesture.connect("released", self.on_device_right_click, mac, name)
            btn.add_controller(gesture)

            self.device_box.append(btn)

    def on_device_right_click(self, gesture, n_press, x, y, mac, name):
        popover = Gtk.Popover()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.set_margin_top(4)
        box.set_margin_bottom(4)
        box.set_margin_start(4)
        box.set_margin_end(4)

        forget_btn = Gtk.Button(label=f"Forget {name}")
        forget_btn.add_css_class("flat")
        forget_btn.add_css_class("error")
        forget_btn.connect("clicked", self.on_forget_device, mac, popover)
        box.append(forget_btn)

        popover.set_child(box)
        widget = gesture.get_widget()
        popover.set_parent(widget)
        popover.popup()

    def on_forget_device(self, btn, mac, popover):
        popover.popdown()
        btn.set_sensitive(False)
        btn.set_label("Removing...")

        def _do():
            run(["bluetoothctl", "disconnect", mac], timeout=5)
            run(["bluetoothctl", "untrust", mac], timeout=5)
            run(["bluetoothctl", "remove", mac], timeout=5)
            GLib.idle_add(self.populate_devices)
        threading.Thread(target=_do, daemon=True).start()

    def on_device_clicked(self, btn, mac, currently_connected):
        btn.set_sensitive(False)
        # Find status label inside button and update it
        btn_box = btn.get_child()
        text_box = btn_box.get_first_child().get_next_sibling()
        status_label = text_box.get_last_child()
        status_label.set_label("Disconnecting..." if currently_connected else "Connecting...")

        def _do():
            if currently_connected:
                bt_disconnect(mac)
            else:
                bt_connect(mac)
            GLib.idle_add(self.populate_devices)

        threading.Thread(target=_do, daemon=True).start()

    def on_power_toggle(self, switch, state):
        def _do():
            bt_toggle_power()
            GLib.idle_add(self.populate_devices)
        threading.Thread(target=_do, daemon=True).start()
        return False

    def on_scan(self, btn):
        if self._scanning:
            return
        self._scanning = True
        self.scan_btn.set_sensitive(False)
        self.spinner_box.set_visible(True)
        self.spinner.start()

        bt_scan_devices(self.on_scan_complete)

    def on_scan_complete(self, new_devices):
        self.spinner.stop()
        self.spinner_box.set_visible(False)
        self.scan_btn.set_sensitive(True)
        self._scanning = False

        # Refresh paired devices too
        self.populate_devices()

        # Clear discovered box
        while child := self.discovered_box.get_first_child():
            self.discovered_box.remove(child)

        if new_devices:
            self.discovered_sep.set_visible(True)
            self.discovered_header.set_visible(True)
            self.discovered_box.set_visible(True)

            for mac, name in new_devices:
                btn = Gtk.Button()
                btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

                icon = Gtk.Image.new_from_icon_name("bluetooth-symbolic")
                btn_box.append(icon)

                label = Gtk.Label(label=name)
                label.set_halign(Gtk.Align.START)
                label.set_hexpand(True)
                label.set_ellipsize(3)
                btn_box.append(label)

                pair_icon = Gtk.Image.new_from_icon_name("list-add-symbolic")
                pair_icon.set_opacity(0.6)
                btn_box.append(pair_icon)

                btn.set_child(btn_box)
                btn.add_css_class("flat")
                btn.add_css_class("device-btn")
                btn.connect("clicked", self.on_pair_device, mac)
                self.discovered_box.append(btn)
        else:
            self.discovered_sep.set_visible(True)
            self.discovered_header.set_visible(True)
            self.discovered_box.set_visible(True)
            label = Gtk.Label(label="No new devices found")
            label.set_opacity(0.5)
            label.set_margin_top(4)
            label.set_margin_bottom(4)
            self.discovered_box.append(label)

    def on_pair_device(self, btn, mac):
        btn.set_sensitive(False)

        def _do():
            run(["bluetoothctl", "pair", mac], timeout=10)
            run(["bluetoothctl", "trust", mac], timeout=5)
            run(["bluetoothctl", "connect", mac], timeout=10)
            GLib.idle_add(self.populate_devices)
        threading.Thread(target=_do, daemon=True).start()

    def on_settings(self, btn):
        subprocess.Popen(["blueman-manager"])
        self.win.close()

    def on_focus_changed(self, win, pspec):
        if self._close_timer:
            GLib.source_remove(self._close_timer)
            self._close_timer = None
        if not win.is_active():
            self._close_timer = GLib.timeout_add(300, self._do_close)

    def _do_close(self):
        if not self.win.is_active():
            self.win.close()
        self._close_timer = None
        return False

    def on_key(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape:
            self.win.close()
            return True
        return False


def main():
    app = BluetoothPopup()
    app.run(sys.argv)


if __name__ == "__main__":
    main()
