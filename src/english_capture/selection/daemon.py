import signal
import sys
import threading
import traceback

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GLib

from ..config import ensure_dirs, DB_PATH
from .. import database as db
from .listener import mouse_listener_thread, keyboard_listener_thread, MouseState
from .overlay import SelectionOverlay
from .capture import capture_from_geometry


class SelectionDaemon:
    def __init__(self):
        self.state = MouseState()
        self.overlay = SelectionOverlay(self.state)
        self._running = False

    def on_select_start(self, state):
        self.overlay.show()

    def on_select_end(self, state):
        with state.lock:
            x1, y1 = state.x1, state.y1
            x2, y2 = state.x2, state.y2
            cancelled = state.cancelled

        def do_capture():
            self.overlay.hide_now()
            if cancelled:
                return
            try:
                capture_from_geometry(x1, y1, x2, y2)
            except Exception as e:
                import subprocess
                subprocess.run(
                    ["notify-send", "-u", "critical", "English Capture error", f"{e}"],
                    timeout=5,
                )

        GLib.idle_add(do_capture)

    def _run_listener(self):
        while self._running:
            try:
                mouse_listener_thread(
                    self.state, self.on_select_start, self.on_select_end
                )
            except Exception:
                traceback.print_exc()
                continue
            break

    def _run_keyboard(self):
        while self._running:
            try:
                keyboard_listener_thread(self.state)
            except Exception:
                traceback.print_exc()
                continue
            break

    def run(self):
        self._running = True
        ensure_dirs()
        db.init_db(DB_PATH)

        mouse = threading.Thread(target=self._run_listener, daemon=True)
        mouse.start()

        kbd = threading.Thread(target=self._run_keyboard, daemon=True)
        kbd.start()

        GLib.timeout_add(33, self._tick)

        signal.signal(signal.SIGINT, signal.SIG_DFL)
        signal.signal(signal.SIGTERM, signal.SIG_DFL)

        from gi.repository import Gtk
        Gtk.main()

    def _tick(self):
        if self.state.is_selecting():
            self.overlay.queue_redraw()
        return True

    def stop(self):
        self._running = False
        from gi.repository import Gtk
        Gtk.main_quit()


def main():
    daemon = SelectionDaemon()
    daemon.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
