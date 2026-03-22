#!/usr/bin/env python3
"""Waybar volume popup — GTK4 + Libadwaita dropdown with slider, mute, and settings."""

import subprocess
import sys
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Gdk", "4.0")
from gi.repository import Gtk, Adw, Gdk, GLib


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True).stdout.strip()


def get_volume():
    out = run(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"])
    # "Volume: 0.75" or "Volume: 0.75 [MUTED]"
    parts = out.split()
    vol = float(parts[1]) if len(parts) >= 2 else 0.0
    muted = "[MUTED]" in out
    return vol, muted


def set_volume(val):
    subprocess.Popen(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{val:.2f}"])


def toggle_mute():
    subprocess.Popen(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"])


def get_sinks():
    """Return list of (id, name, is_default) for audio sinks."""
    default = run(["pactl", "get-default-sink"])
    out = run(["pactl", "list", "sinks", "short"])
    sinks = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            sink_id = parts[0]
            sink_name = parts[1]
            # Get description
            desc = run(["pactl", "list", "sinks"]).split(f"Name: {sink_name}")
            friendly = sink_name
            if len(desc) > 1:
                for d_line in desc[1].splitlines():
                    if "Description:" in d_line:
                        friendly = d_line.split("Description:")[1].strip()
                        break
            sinks.append((sink_id, sink_name, friendly, sink_name == default))
    return sinks


class VolumePopup(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.waybar.volume-popup")
        self.connect("activate", self.on_activate)
        self._updating = False

    def on_activate(self, app):
        # Kill existing instance
        self.win = Adw.ApplicationWindow(application=app)
        self.win.set_default_size(320, -1)
        self.win.set_resizable(False)
        self.win.set_title("Volume")

        # Make it float like a popup
        self.win.set_decorated(False)

        # Main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        main_box.add_css_class("main-box")

        # Header with title and settings button
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header_box.set_margin_start(16)
        header_box.set_margin_end(8)
        header_box.set_margin_top(12)
        header_box.set_margin_bottom(4)

        title = Gtk.Label(label="Sound")
        title.add_css_class("title-3")
        title.set_hexpand(True)
        title.set_halign(Gtk.Align.START)
        header_box.append(title)

        settings_btn = Gtk.Button()
        settings_btn.set_icon_name("emblem-system-symbolic")
        settings_btn.add_css_class("flat")
        settings_btn.add_css_class("circular")
        settings_btn.set_tooltip_text("Sound Settings")
        settings_btn.connect("clicked", self.on_settings)
        header_box.append(settings_btn)

        main_box.append(header_box)

        # Volume control row
        vol_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        vol_box.set_margin_start(16)
        vol_box.set_margin_end(16)
        vol_box.set_margin_top(8)
        vol_box.set_margin_bottom(8)

        # Mute button
        self.mute_btn = Gtk.Button()
        self.mute_btn.add_css_class("flat")
        self.mute_btn.add_css_class("circular")
        self.mute_btn.connect("clicked", self.on_mute)
        vol_box.append(self.mute_btn)

        # Volume slider
        self.scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 1.0, 0.01)
        self.scale.set_hexpand(True)
        self.scale.set_draw_value(False)
        self.scale.connect("value-changed", self.on_volume_changed)
        vol_box.append(self.scale)

        # Percentage label
        self.vol_label = Gtk.Label()
        self.vol_label.set_width_chars(4)
        self.vol_label.add_css_class("caption")
        vol_box.append(self.vol_label)

        main_box.append(vol_box)

        # Separator
        main_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # Output device section
        device_header = Gtk.Label(label="Output Device")
        device_header.add_css_class("caption")
        device_header.set_halign(Gtk.Align.START)
        device_header.set_margin_start(16)
        device_header.set_margin_top(8)
        device_header.set_margin_bottom(4)
        device_header.set_opacity(0.7)
        main_box.append(device_header)

        # Device list
        self.device_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.device_box.set_margin_start(8)
        self.device_box.set_margin_end(8)
        self.device_box.set_margin_bottom(12)
        main_box.append(self.device_box)

        self.populate_devices()
        self.update_ui()

        # CSS
        css = Gtk.CssProvider()
        css.load_from_string("""
            .main-box {
                background-color: alpha(@window_bg_color, 0.95);
            }
            scale trough {
                min-height: 8px;
                border-radius: 4px;
            }
            scale highlight {
                border-radius: 4px;
            }
            .device-btn {
                padding: 8px 12px;
                border-radius: 8px;
            }
            .device-btn.active {
                background-color: alpha(@accent_color, 0.15);
            }
        """)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.win.set_content(main_box)

        # Auto-refresh volume every 500ms
        GLib.timeout_add(500, self.update_ui)

        # Close on focus loss — with delay to avoid closing during mouse transit
        self._close_timer = None
        self.win.connect("notify::is-active", self.on_focus_changed)

        # Close on Escape
        esc = Gtk.EventControllerKey()
        esc.connect("key-pressed", self.on_key)
        self.win.add_controller(esc)

        self.win.present()

    def populate_devices(self):
        # Clear
        while child := self.device_box.get_first_child():
            self.device_box.remove(child)

        sinks = get_sinks()
        for sink_id, sink_name, friendly, is_default in sinks:
            btn = Gtk.Button()
            btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

            icon = Gtk.Image.new_from_icon_name(
                "audio-speakers-symbolic" if "analog" in sink_name else "audio-headphones-symbolic"
            )
            btn_box.append(icon)

            # Truncate long names
            display_name = friendly if len(friendly) <= 40 else friendly[:37] + "..."
            label = Gtk.Label(label=display_name)
            label.set_halign(Gtk.Align.START)
            label.set_hexpand(True)
            label.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
            btn_box.append(label)

            if is_default:
                check = Gtk.Image.new_from_icon_name("object-select-symbolic")
                btn_box.append(check)
                btn.add_css_class("active")

            btn.set_child(btn_box)
            btn.add_css_class("flat")
            btn.add_css_class("device-btn")
            btn.connect("clicked", self.on_device_selected, sink_name)
            self.device_box.append(btn)

    def update_ui(self):
        vol, muted = get_volume()
        self._updating = True
        self.scale.set_value(vol)
        self._updating = False

        pct = int(vol * 100)
        self.vol_label.set_text(f"{pct}%")

        if muted:
            self.mute_btn.set_icon_name("audio-volume-muted-symbolic")
            self.scale.set_sensitive(False)
        else:
            if pct == 0:
                self.mute_btn.set_icon_name("audio-volume-muted-symbolic")
            elif pct < 33:
                self.mute_btn.set_icon_name("audio-volume-low-symbolic")
            elif pct < 66:
                self.mute_btn.set_icon_name("audio-volume-medium-symbolic")
            else:
                self.mute_btn.set_icon_name("audio-volume-high-symbolic")
            self.scale.set_sensitive(True)

        return True  # keep timeout

    def on_volume_changed(self, scale):
        if self._updating:
            return
        val = scale.get_value()
        set_volume(val)
        pct = int(val * 100)
        self.vol_label.set_text(f"{pct}%")

    def on_mute(self, btn):
        toggle_mute()
        self.update_ui()

    def on_settings(self, btn):
        subprocess.Popen(["pavucontrol"])
        self.win.close()

    def on_device_selected(self, btn, sink_name):
        subprocess.run(["pactl", "set-default-sink", sink_name])
        self.populate_devices()

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
    app = VolumePopup()
    app.run(sys.argv)


if __name__ == "__main__":
    main()
