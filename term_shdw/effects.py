import sys
import time
import random
from .utils import rgb_to_ansi, lerp_color, get_terminal_size

SYMBOLS = ['+', ' ']
HEAD_OFFSET = [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]
STAR_SYMBOLS = ['.', '+', '*']
STAR_SPAWN_CHANCE = 0.02
MAX_STAR_AGE = 4
NUM_MAX_STARS = 100

stars = []

def draw_head(x, y, symbol, head_rgb):
    for dx, dy in HEAD_OFFSET:
        cx, cy = x + dx, y + dy
        col = cx - len(symbol) // 2
        if col < 1:
            col = 1
        sys.stdout.write(f"\033[{cy};{col}H{rgb_to_ansi(*head_rgb)}{symbol}\033[1m")

def draw_tail(trail, head_rgb, tail_rgb):
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

        r, g, b = lerp_color(head_rgb, tail_rgb, t_color)
        color_code = rgb_to_ansi(r, g, b)

        if i < 5:
            sys.stdout.write(f"\033[{y};{x}H{color_code}{symbol}\033[1m")
        elif i < 8:
            for dx in [0, 1]:
                sys.stdout.write(f"\033[{y};{x+dx}H{color_code}{symbol}\033[1m"*2)
        else:
            for dy in [-1, 0, 0]:
                for dx in [-1, 0, 1]:
                    sys.stdout.write(f"\033[{y+dy};{x+dx}H{color_code}{symbol}\033[1m")

def draw_aura(x, y, symbol_width, symbol_height, tail_rgb, term_width, term_height):
    col_center = x - symbol_width // 2
    width = symbol_width
    height = symbol_height

    for cy in range(y - 2, y + height + 2):
        for cx in range(col_center - 2, col_center + width + 2):
            if y <= cy < y + height and col_center <= cx < col_center + width:
                continue
            if (cx == col_center - 2 or cx == col_center + width + 1) and (cy == y - 2 or cy == y + height + 1):
                continue
            if 1 <= cx <= term_width and 1 <= cy <= term_height:
                sys.stdout.write(f"\033[{cy};{cx}H{rgb_to_ansi(*tail_rgb)}+\033[1m")

def draw_stars(term_width=None, term_height=None):
    global stars
    now = time.time()

    if term_width is None or term_height is None:
        term_width, term_height = get_terminal_size()

    if len(stars) < NUM_MAX_STARS and random.random() < STAR_SPAWN_CHANCE:
        sx = random.randint(1, max(1, term_width))
        sy = random.randint(1, max(1, term_height))
        symbol = random.choice(STAR_SYMBOLS)
        stars.append((sx, sy, now, symbol))

    new_stars = []
    for (x, y, t, symbol) in stars:
        age = now - t
        if age < MAX_STAR_AGE:
            if 1 <= x <= term_width and 1 <= y <= term_height:
                sys.stdout.write(f"\033[{y};{x}H\033[97m{symbol}\033[0m")
            new_stars.append((x, y, t, symbol))
    stars = new_stars
