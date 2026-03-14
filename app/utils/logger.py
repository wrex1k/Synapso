import logging
import os
import sys
from logging.handlers import RotatingFileHandler

"""
This module provides a logging utility that sets up a logger with both console and file handlers. It includes:
- WindowsSafeRotatingFileHandler: a custom file handler that handles file locking issues on Windows during log rotation
- ColorFormatter: a formatter that adds ANSI color codes to console log messages based on log level
- LevelListFilter: a filter that allows only specified log levels to be emitted
- _enable_windows_ansi_colors: a helper function to enable ANSI colors in Windows console
- _parse_log_levels_env: a helper function to parse allowed log levels from the LOG_LEVEL
"""

class WindowsSafeRotatingFileHandler(RotatingFileHandler):
    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None

        try:
            super().doRollover()
        except PermissionError:
            pass
        finally:
            if not self.stream:
                self.stream = self._open()


class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[37m",     # gray
        logging.INFO: "\033[36m",      # cyan
        logging.WARNING: "\033[33m",   # yellow
        logging.ERROR: "\033[31m",     # red
        logging.CRITICAL: "\033[41m",  # red background
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        color = self.COLORS.get(record.levelno, "")
        reset = self.RESET if color else ""
        return f"{color}{msg}{reset}"


class LevelListFilter(logging.Filter):
    def __init__(self, allowed_levels: set[int]):
        super().__init__()
        self.allowed_levels = allowed_levels

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno in self.allowed_levels


def _enable_windows_ansi_colors() -> None:
    if sys.platform == "win32":
        try:
            os.system("")
        except Exception:
            pass


def _parse_log_levels_env() -> set[int] | None:
    raw = os.getenv("LOG_LEVELS", "").strip()
    if not raw:
        return None

    allowed: set[int] = set()
    for name in [x.strip().upper() for x in raw.split(",") if x.strip()]:
        lvl = logging._nameToLevel.get(name)
        if lvl is not None:
            allowed.add(lvl)

    return allowed or None


def get_logger(name: str = "synapso") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    _enable_windows_ansi_colors()

    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    log_dir = os.getenv("LOG_DIR", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, os.getenv("LOG_FILE", "app.log"))

    console_formatter = ColorFormatter(
        fmt="%(asctime)s %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )

    file_formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s | %(module)s.%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    max_bytes = int(os.getenv("LOG_MAX_BYTES", "1048576"))
    backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))

    if sys.platform == "win32":
        file_handler = WindowsSafeRotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
    else:
        pass

    console_handler = logging.StreamHandler()

    file_handler.setLevel(logging.DEBUG)
    console_handler.setLevel(logging.DEBUG)

    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)

    allowed_levels = _parse_log_levels_env()
    if allowed_levels is not None:
        lvl_filter = LevelListFilter(allowed_levels)
        file_handler.addFilter(lvl_filter)
        console_handler.addFilter(lvl_filter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger