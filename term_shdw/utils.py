import os

def hex_to_rgb(hex_color: str):
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (r, g, b)

def rgb_to_ansi(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"

def hex_to_ansi(hex_color: str):
    r, g, b = hex_to_rgb(hex_color)
    return rgb_to_ansi(r, g, b)

def lerp(a, b, t):
    return int(a + (b - a) * t)

def lerp_color(c1, c2, t):
    return (
        lerp(c1[0], c2[0], t),
        lerp(c1[1], c2[1], t),
        lerp(c1[2], c2[2], t),
    )

def get_terminal_size():
    try:
        rows, cols = os.popen('stty size', 'r').read().split()
        return int(cols), int(rows)
    except:
        return 80, 24
