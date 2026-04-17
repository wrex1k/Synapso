"""UI font scaling based on window size."""

_BASE_WIDTH = 1600
_BASE_HEIGHT = 1000
_main_window = None

def set_main_window(window):
    """Set reference to main window for size-based scaling."""
    global _main_window
    _main_window = window

def get_dpi_scale() -> float:
    """Get scale factor based on current window size vs base size."""
    if _main_window is not None:
        w = _main_window.width()
        h = _main_window.height()
        if w > 0 and h > 0:
            ratio = (w / _BASE_WIDTH + h / _BASE_HEIGHT) / 2
            return max(0.75, min(1.6, ratio))

    return 1.0

def scale_font(base_size: int) -> int:
    """Scale font size based on window size."""
    return max(8, int(base_size * get_dpi_scale()))
