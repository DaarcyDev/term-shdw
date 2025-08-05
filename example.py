import sys
import tty
import termios
import atexit
import os
import time
import select
import random

MAX_TRAIL_LENGTH = 20
FRAME_DELAY = 0.0001
SYMBOLS = ['+', ' ']
HEAD_SYMBOL = '{#@#}'
HEAD_OFFSET = [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]

STAR_SYMBOLS = ['.', '+', '*']
STAR_SPAWN_CHANCE = 0.02
MAX_STAR_AGE = 4
NUM_MAX_STARS = 100

def hex_to_rgb(hex_color: str):
    """Convert hex color string to (r, g, b) tuple."""
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (r, g, b)

def rgb_to_ansi(r, g, b):
    """Convert (r, g, b) values to ANSI escape code for 24-bit color."""
    return f"\033[38;2;{r};{g};{b}m"

def hex_to_ansi(hex_color: str):
    """Convert hex color string directly to ANSI escape code."""
    r, g, b = hex_to_rgb(hex_color)
    return rgb_to_ansi(r, g, b)

def lerp(a, b, t):
    """Linear interpolation between values a and b by t."""
    return int(a + (b - a) * t)

def lerp_color(c1, c2, t):
    """Linear interpolation between two RGB colors."""
    return (
        lerp(c1[0], c2[0], t),
        lerp(c1[1], c2[1], t),
        lerp(c1[2], c2[2], t),
    )

COLOR_HEAD = hex_to_ansi("681414")
COLOR_TAIL = hex_to_ansi("7b87ed")
COLOR_HEAD_RGB = hex_to_rgb("681414")
COLOR_TAIL_RGB = hex_to_rgb("7b87ed")
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"
WHITE = "\033[97m"

fd = sys.stdin.fileno()
old_settings = termios.tcgetattr(fd)
tty.setcbreak(fd)
atexit.register(lambda: termios.tcsetattr(fd, termios.TCSADRAIN, old_settings))

sys.stdout.write("\033[?1003h")  # Enable mouse tracking
sys.stdout.write("\033[2J\033[H")  # Clear screen and move cursor home
sys.stdout.write("\033[?25l")  # Hide cursor
sys.stdout.flush()

print("Move the mouse over the terminal. Comet effect. (Ctrl+C to exit)")

trail = []
stars = []
last_pos = (0, 0)
last_mouse_time = time.time()

def get_terminal_size():
    """Get current terminal width and height."""
    try:
        rows, cols = os.popen('stty size', 'r').read().split()
        return int(cols), int(rows)
    except:
        return 80, 24

term_width, term_height = get_terminal_size()

def decode_mouse_coords(data: bytes):
    """Decode mouse event coordinates from bytes."""
    return data[1] - 32, data[2] - 32

def draw_head(x, y):
    """Draw comet head at (x, y) with configured color."""
    for dx, dy in HEAD_OFFSET:
        cx, cy = x + dx, y + dy
        col = cx - len(HEAD_SYMBOL) // 2
        sys.stdout.write(f"\033[{cy};{col}H{COLOR_HEAD}{HEAD_SYMBOL}{COLOR_BOLD}")

def draw_tail(trail):
    """Draw fading comet tail with smooth disappearance."""
    now = time.time()
    max_age = 0.5
    length = len(trail)

    for i, (x, y, t) in enumerate(trail):
        age = now - t
        if age > max_age:
            continue
        
        t_linear = age / max_age
        t_eased = 1 - (1 - t_linear) ** 2
        
        idx = int(t_eased * len(SYMBOLS))
        idx = min(idx, len(SYMBOLS) - 1)
        symbol = SYMBOLS[idx]

        t_color = 1 - (i / max(length - 1, 1))

        r, g, b = lerp_color(COLOR_HEAD_RGB, COLOR_TAIL_RGB, t_color)
        color_code = rgb_to_ansi(r, g, b)

        if i < 5:
            sys.stdout.write(f"\033[{y};{x}H{color_code}{symbol}{COLOR_BOLD}")
        elif i < 8:
            for dx in [0, 1]:
                sys.stdout.write(f"\033[{y};{x+dx}H{color_code}{symbol}{COLOR_BOLD}")
        else:
            for dy in [-1, 0, 0]:
                for dx in [-1, 0, 1]:
                    sys.stdout.write(f"\033[{y+dy};{x+dx}H{color_code}{symbol}{COLOR_BOLD}")

def draw_aura(x, y):
    """Draw light blue aura around the comet head without corners."""
    col_center = x - len(HEAD_SYMBOL) // 2
    width = len(HEAD_SYMBOL)
    height = 1
    
    for cy in range(y - 2, y + height + 2):
        for cx in range(col_center - 2, col_center + width + 2):
            if y <= cy < y + height and col_center <= cx < col_center + width:
                continue
            
            if (cx == col_center - 2 or cx == col_center + width + 1) and (cy == y - 2 or cy == y + height + 1):
                continue
            
            if 1 <= cx <= term_width and 1 <= cy <= term_height:
                sys.stdout.write(f"\033[{cy};{cx}H{COLOR_TAIL}+{COLOR_BOLD}")

def draw_stars():
    """Draw twinkling stars and regenerate them."""
    now = time.time()
    global stars

    if len(stars) < NUM_MAX_STARS and random.random() < STAR_SPAWN_CHANCE:
        sx = random.randint(1, term_width)
        sy = random.randint(1, term_height)
        symbol = random.choice(STAR_SYMBOLS)
        stars.append((sx, sy, now, symbol))

    new_stars = []
    for (x, y, t, symbol) in stars:
        age = now - t
        if age < MAX_STAR_AGE:
            sys.stdout.write(f"\033[{y};{x}H{WHITE}{symbol}{COLOR_RESET}")
            new_stars.append((x, y, t, symbol))
    stars = new_stars

try:
    while True:
        now = time.time()

        rlist, _, _ = select.select([sys.stdin], [], [], 0.01)
        if rlist:
            ch = sys.stdin.buffer.read(1)
            if ch == b'\x1b':
                seq = sys.stdin.buffer.read(2)
                if seq == b'[M':
                    coords = sys.stdin.buffer.read(3)
                    x, y = decode_mouse_coords(coords)

                    if (x, y) != last_pos:
                        head_width = len(HEAD_SYMBOL)
                        head_height = 1

                        x = max(head_width // 2 + 1, x)
                        x = min(term_width - (head_width // 2), x)

                        y = max(1, y)
                        y = min(term_height - head_height, y)

                        last_pos = (x, y)
                        last_mouse_time = now
                        trail.append((x, y, now))
                        if len(trail) > MAX_TRAIL_LENGTH:
                            trail.pop(0)

        sys.stdout.write("\033[2J")

        draw_stars()

        INACTIVITY_TIMEOUT = 0.4
        if time.time() - last_mouse_time < INACTIVITY_TIMEOUT and last_pos != (0, 0):
            if trail:
                draw_tail(trail)
            draw_head(*last_pos)
        else:
            if last_pos != (0, 0):
                draw_aura(*last_pos)
                draw_head(*last_pos)

        sys.stdout.flush()

        trail = [(x, y, t) for (x, y, t) in trail if now - t < 2.0]

        time.sleep(FRAME_DELAY)

except KeyboardInterrupt:
    sys.stdout.write("\033[?1003l\033[?25h")
    sys.stdout.write("\033[0m\nClean exit.\n")
    sys.stdout.flush()
