import gi
gi.require_version("Gtk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import Gtk, Gdk, GLib, GtkLayerShell

import cairo


class SelectionOverlay:
    def __init__(self, state):
        self.state = state
        self._visible = False

        self.win = Gtk.Window.new(Gtk.WindowType.TOPLEVEL)
        self.win.set_title("english-capture-selection")
        self.win.set_decorated(False)
        self.win.set_app_paintable(True)

        GtkLayerShell.init_for_window(self.win)
        GtkLayerShell.set_layer(self.win, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_namespace(self.win, "selection")
        GtkLayerShell.set_exclusive_zone(self.win, 0)
        GtkLayerShell.set_keyboard_mode(self.win, GtkLayerShell.KeyboardMode.NONE)
        GtkLayerShell.set_anchor(self.win, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_anchor(self.win, GtkLayerShell.Edge.BOTTOM, True)
        GtkLayerShell.set_anchor(self.win, GtkLayerShell.Edge.LEFT, True)
        GtkLayerShell.set_anchor(self.win, GtkLayerShell.Edge.RIGHT, True)

        self.win.set_events(
            Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.KEY_PRESS_MASK
        )

        screen = self.win.get_screen()
        rgba = screen.get_rgba_visual()
        if rgba:
            self.win.set_visual(rgba)

        self.win.connect("draw", self.on_draw)
        self.win.connect("key-press-event", self.on_key_press)
        self.win.connect("screen-changed", self.on_screen_changed)

    def on_screen_changed(self, widget, previous_screen):
        screen = widget.get_screen()
        rgba = screen.get_rgba_visual()
        if rgba:
            widget.set_visual(rgba)

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            with self.state.lock:
                self.state.cancelled = True
                self.state.selecting = False
                self.state.button_down = False
            self.hide()
        return True

    def on_draw(self, widget, cr):
        cr.set_source_rgba(0, 0, 0, 0)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()

        with self.state.lock:
            selecting = self.state.selecting
            if not selecting:
                return
            x1, y1 = self.state.x1, self.state.y1
            x2, y2 = self.state.x2, self.state.y2
            cancelled = self.state.cancelled

        if cancelled or not selecting:
            return

        rx1 = min(x1, x2)
        ry1 = min(y1, y2)
        rw = abs(x2 - x1)
        rh = abs(y2 - y1)

        if rw < 2 and rh < 2:
            return

        win_w = widget.get_allocated_width()
        win_h = widget.get_allocated_height()

        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgba(0, 0, 0, 0.28)
        cr.paint()

        cr.set_operator(cairo.OPERATOR_CLEAR)
        cr.rectangle(rx1, ry1, rw, rh)
        cr.fill()

        cr.set_operator(cairo.OPERATOR_OVER)
        cr.set_source_rgba(1, 1, 1, 0.95)
        cr.set_line_width(2.5)
        cr.rectangle(rx1, ry1, rw, rh)
        cr.stroke()

        hl = rw > 30 and rh > 30
        if hl:
            cx = rx1 + rw / 2
            cy = ry1 + rh / 2
            cr.set_source_rgba(1, 1, 1, 0.2)
            cr.set_line_width(1)
            cr.set_dash([4, 6])
            cr.move_to(cx, ry1)
            cr.line_to(cx, ry1 + rh)
            cr.stroke()
            cr.move_to(rx1, cy)
            cr.line_to(rx1 + rw, cy)
            cr.stroke()
            cr.set_dash([])

        txt = f"{rw}x{rh}"
        cr.set_source_rgba(1, 1, 1, 0.85)
        cr.select_font_face("monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(13)
        tx = rx1
        ty = ry1 - 8
        if ty < 12:
            ty = ry1 + rh + 16
        cr.move_to(tx, ty)
        cr.show_text(txt)

        return True

    def show(self):
        if self._visible:
            return
        self._visible = True
        GLib.idle_add(self._show_impl)

    def _show_impl(self):
        self.win.show_all()
        return False

    def hide(self):
        if not self._visible:
            return
        self._visible = False
        GLib.idle_add(self._hide_impl)

    def hide_now(self):
        if not self._visible:
            return
        self._visible = False
        self._hide_impl()

    def _hide_impl(self):
        self.win.hide()
        return False

    def queue_redraw(self):
        if self._visible:
            GLib.idle_add(self.win.queue_draw)
