from gas.color import Color
import colorsys
import random


# Makes color blue by sorting r/g/b
def make_color_blue(color: Color) -> Color:
    a, r, g, b = color.get_argb()
    r, g, b = sorted([r, g, b])
    return Color.from_argb(a, r, g, b)


def make_color_half_gray(color: Color) -> Color:
    a, r, g, b = color.get_argb()
    rgb_avg = (r + g + b) / 3
    r = int((r + rgb_avg) / 2)
    g = int((g + rgb_avg) / 2)
    b = int((b + rgb_avg) / 2)
    return Color.from_argb(a, r, g, b)


def invert_color_hue(color: Color) -> Color:
    a, r, g, b = color.get_argb()
    r, g, b = [x / 255 for x in (r, g, b)]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    h += 0.5
    if h > 1:
        h -= 1
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    r, g, b = [int(x * 255) for x in (r, g, b)]
    return Color.from_argb(a, r, g, b)


# for mickeymouse lighting (preserves saturation & brightness value tho)
def randomize_color_hue(color: Color) -> Color:
    a, r, g, b = color.get_argb()
    r, g, b = [x / 255 for x in (r, g, b)]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    h = random.random()  # random float between 0 and 1
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    r, g, b = [int(x * 255) for x in (r, g, b)]
    return Color.from_argb(a, r, g, b)


# tone down colors by cutting saturation in half
def make_color_bleaker(color: Color) -> Color:
    a, r, g, b = color.get_argb()
    r, g, b = [x / 255 for x in (r, g, b)]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    s /= 2
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    r, g, b = [int(x * 255) for x in (r, g, b)]
    return Color.from_argb(a, r, g, b)
