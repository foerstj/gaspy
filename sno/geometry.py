def triangle_2d_area(x1, y1, x2, y2, x3, y3):
    return abs((x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2)) / 2.0)


def is_point_inside_triangle_2d(x1, y1, x2, y2, x3, y3, x, y):
    # Calculate area of triangle ABC
    a = triangle_2d_area(x1, y1, x2, y2, x3, y3)

    # Calculate area of triangle PBC
    a1 = triangle_2d_area(x, y, x2, y2, x3, y3)
    # Calculate area of triangle PAC
    a2 = triangle_2d_area(x1, y1, x, y, x3, y3)
    # Calculate area of triangle PAB
    a3 = triangle_2d_area(x1, y1, x2, y2, x, y)

    # Check if sum of A1, A2 and A3
    # is same as A
    return a == a1 + a2 + a3
