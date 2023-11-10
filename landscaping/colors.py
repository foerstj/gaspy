from gas.color import Color


# Makes color blue by sorting r/g/b
def make_color_blue(color: Color) -> Color:
    a, r, g, b = color.get_argb()
    r, g, b = sorted([r, g, b])
    return Color.from_argb(a, r, g, b)
