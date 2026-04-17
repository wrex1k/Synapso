from PySide6.QtWidgets import QWidget

from app.utils.window import window_resize
from app.utils.logger import get_logger
logger = get_logger(__name__)


# common screen resolutions for testing
screen_resolutions = {
    # standard displays
    "small": (1280, 720),      # Small HD
    "hd": (1366, 768),         # HD (most common laptop)
    "wxga": (1440, 900),       # WXGA+
    "hd+": (1600, 900),        # HD+
    "fhd": (1920, 1080),       # Full HD
    "wuxga": (1920, 1200),     # WUXGA
    "qhd": (2560, 1440),       # QHD/2K
    "4k": (3840, 2160),        # 4K UHD
    "5k": (5120, 2880),        # 5K (iMac 27")
    
    # ultra Wide displays (21:9 and 32:9)
    "uwfhd": (2560, 1080),     # UltraWide FHD (21:9)
    "uwqhd": (3440, 1440),     # UltraWide QHD (21:9)
    "uw4k": (3840, 1600),      # UltraWide 4K (24:10)
    "superuw": (5120, 2160),   # Super UltraWide (32:9)
}

def simulate_resolution(window: QWidget, resolution: str = "hd"):
    if resolution.lower() in screen_resolutions:
        width, height = screen_resolutions[resolution.lower()]
    elif "x" in resolution:
        try:
            width, height = map(int, resolution.lower().split("x"))
        except ValueError:
            logger.error("Invalid resolution format: %s", resolution)
            return
    else:
        logger.error("Unknown resolution: %s", resolution)
        logger.info("Available presets: %s", ", ".join(screen_resolutions.keys()))
        return
    
    window_resize(window, width, height, lock_size=True)
    logger.warning("Simulating resolution: %dx%d (size locked for testing)", width, height)