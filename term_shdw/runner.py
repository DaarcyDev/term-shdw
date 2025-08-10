import sys, tty, termios, atexit, select, time
from .effects import draw_head, draw_tail, draw_aura, draw_stars
from .utils import hex_to_rgb, get_terminal_size
from .config import get_config

def _enable_mouse_modes():
    sys.stdout.write("\033[?1003h\033[?1006h")
    sys.stdout.flush()

def _disable_mouse_modes():
    sys.stdout.write("\033[?1003l\033[?1006l")
    sys.stdout.flush()

def _parse_mouse_event_buffer(buf):
    if not buf:
        return None

    if buf.startswith(b'[M'):
        if len(buf) >= 5:
            coords = buf[2:5]
            try:
                x = coords[1] - 32
                y = coords[2] - 32
                return x, y
            except Exception:
                return None
        return None

    if buf.startswith(b'[<'):
        try:
            s = buf[2:].decode(errors='ignore')
            if s.endswith('M') or s.endswith('m'):
                s = s[:-1]
            parts = s.split(';')
            if len(parts) >= 3:
                x = int(parts[1])
                y = int(parts[2])
                return x, y
        except Exception:
            return None

    return None

def run():
    args = get_config()

    head_rgb = hex_to_rgb(args.color_head)
    tail_rgb = hex_to_rgb(args.color_tail)

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    atexit.register(lambda: termios.tcsetattr(fd, termios.TCSADRAIN, old_settings))

    _enable_mouse_modes()
    sys.stdout.write("\033[2J\033[H\033[?25l")
    sys.stdout.flush()

    trail = []
    last_pos = (0, 0)
    last_mouse_time = time.time()

    try:
        while True:
            term_width, term_height = get_terminal_size()

            rlist, _, _ = select.select([sys.stdin], [], [], 0.01)
            if rlist:
                ch = sys.stdin.buffer.read(1)
                if ch == b'\x1b':
                    next1 = sys.stdin.buffer.read(1)
                    if next1 != b'[':
                        continue

                    peek = sys.stdin.buffer.read(1)
                    if peek == b'M':
                        coords = sys.stdin.buffer.read(3)
                        buf = b'[' + b'M' + coords
                        parsed = _parse_mouse_event_buffer(buf)
                    elif peek == b'<':
                        data = bytearray(b'[<')
                        while True:
                            bch = sys.stdin.buffer.read(1)
                            if not bch:
                                break
                            data += bch
                            if bch in (b'M', b'm'):
                                break
                        parsed = _parse_mouse_event_buffer(bytes(data))
                    else:
                        continue

                    if parsed:
                        x, y = parsed

                        head_width = len(args.symbol_head)
                        head_height = 1

                        x = max(head_width // 2 + 1, x)
                        x = min(term_width - (head_width // 2), x)

                        y = max(1, y)
                        y = min(term_height - head_height, y)

                        last_pos = (x, y)
                        last_mouse_time = time.time()
                        trail.append((x, y, time.time()))
                        if len(trail) > args.trail_length:
                            trail.pop(0)

            sys.stdout.write("\033[2J")

            draw_stars(term_width=term_width, term_height=term_height)

            INACTIVITY_TIMEOUT = 0.4
            if time.time() - last_mouse_time < INACTIVITY_TIMEOUT and last_pos != (0, 0):
                if trail:
                    draw_tail(trail, head_rgb, tail_rgb)
                draw_head(*last_pos, args.symbol_head, head_rgb)
            else:
                if last_pos != (0, 0):
                    draw_aura(last_pos[0], last_pos[1], len(args.symbol_head), 1, tail_rgb, term_width, term_height)
                    draw_head(*last_pos, args.symbol_head, head_rgb)

            sys.stdout.flush()
            trail = [(x, y, t) for (x, y, t) in trail if time.time() - t < 2.0]
            time.sleep(args.frame_delay)

    except KeyboardInterrupt:
        _disable_mouse_modes()
        sys.stdout.write("\033[?25h\033[0m\n")
        sys.stdout.flush()
    except Exception as e:
        _disable_mouse_modes()
        raise
