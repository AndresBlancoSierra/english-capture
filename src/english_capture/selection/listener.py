import math
import subprocess
import threading
import evdev
from evdev import ecodes

DRAG_THRESHOLD = 15

class MouseState:
    def __init__(self):
        self.lock = threading.Lock()
        self.button_down = False
        self.selecting = False
        self.x1 = 0
        self.y1 = 0
        self.x2 = 0
        self.y2 = 0
        self.rel_dx = 0
        self.rel_dy = 0
        self.cancelled = False

    def copy_positions(self):
        with self.lock:
            return self.x1, self.y1, self.x2, self.y2

    def is_selecting(self):
        with self.lock:
            return self.selecting


def get_cursor_pos():
    result = subprocess.run(
        ["hyprctl", "cursorpos"], capture_output=True, text=True, timeout=2
    )
    parts = result.stdout.strip().split(",")
    return int(parts[0].strip()), int(parts[1].strip())


def find_mouse_device():
    candidates = []
    for path in evdev.list_devices():
        dev = evdev.InputDevice(path)
        caps = dev.capabilities()
        has_middle = ecodes.BTN_MIDDLE in caps.get(ecodes.EV_KEY, [])
        has_rel_x = ecodes.REL_X in caps.get(ecodes.EV_REL, [])
        if has_middle and has_rel_x:
            is_virtual = "virtual" in dev.name.lower() or "keyd" in dev.name.lower()
            candidates.append((is_virtual, dev))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]


def find_keyboard_device():
    for path in evdev.list_devices():
        dev = evdev.InputDevice(path)
        caps = dev.capabilities()
        if ecodes.KEY_ESC in caps.get(ecodes.EV_KEY, []):
            has_letters = any(k >= ecodes.KEY_A and k <= ecodes.KEY_Z for k in caps.get(ecodes.EV_KEY, []))
            if has_letters:
                return dev
    return None


def mouse_listener_thread(state, on_select_start, on_select_end):
    dev = find_mouse_device()
    if dev is None:
        print("mouse listener: no mouse device found")
        return

    base_x = 0
    base_y = 0
    notified = False

    while True:
        try:
            for event in dev.read_loop():
                if event.type == ecodes.EV_KEY:
                    if event.code == ecodes.BTN_MIDDLE:
                        if event.value == 1:
                            with state.lock:
                                state.button_down = True
                                state.selecting = False
                                state.rel_dx = 0
                                state.rel_dy = 0
                                state.cancelled = False
                                notified = False
                            base_x, base_y = get_cursor_pos()

                        elif event.value == 0:
                            with state.lock:
                                was_selecting = state.selecting
                                was_cancelled = state.cancelled
                                state.button_down = False
                                state.selecting = False

                            if was_selecting and not was_cancelled:
                                end_x, end_y = get_cursor_pos()
                                with state.lock:
                                    state.x2 = end_x
                                    state.y2 = end_y
                                on_select_end(state)
                            notified = False

                elif event.type == ecodes.EV_REL:
                    with state.lock:
                        if not state.button_down:
                            continue
                        if event.code == ecodes.REL_X:
                            state.rel_dx += event.value
                        elif event.code == ecodes.REL_Y:
                            state.rel_dy += event.value

                        if not state.selecting:
                            dist = math.sqrt(state.rel_dx ** 2 + state.rel_dy ** 2)
                            if dist > DRAG_THRESHOLD:
                                state.selecting = True
                                state.x1 = base_x
                                state.y1 = base_y
                                state.x2 = base_x + state.rel_dx
                                state.y2 = base_y + state.rel_dy
                        else:
                            state.x2 = base_x + state.rel_dx
                            state.y2 = base_y + state.rel_dy

                    with state.lock:
                        should_notify = state.selecting and not state.cancelled and not notified
                    if should_notify:
                        notified = True
                        on_select_start(state)

        except OSError as e:
            if not state.button_down and not state.selecting:
                import time
                time.sleep(1)
                continue
            raise


def keyboard_listener_thread(state):
    dev = find_keyboard_device()
    if dev is None:
        return

    while True:
        try:
            for event in dev.read_loop():
                if event.type == ecodes.EV_KEY and event.value == 1:
                    if event.code == ecodes.KEY_ESC:
                        with state.lock:
                            if state.selecting:
                                state.cancelled = True
                                state.selecting = False
                                state.button_down = False
        except OSError:
            import time
            time.sleep(1)
            continue
