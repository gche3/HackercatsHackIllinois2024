
def interpolate(x0, y0, x1, y1, y_target):
    """solve for x by linear interpolation."""
    frac = (y_target - y0) / (y1 - y0)
    return frac * (x1 - x0) + x0
