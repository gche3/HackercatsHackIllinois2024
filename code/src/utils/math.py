
def interpolate(x0, y0, x1, y1, x_target):
    """solve for x by linear interpolation."""
    frac = (x_target - x0) / (x1 - x0)
    return frac * (y1 - y0) + y0
