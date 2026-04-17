import logging
import os
import re
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


_current_user_id: str | None = None


def set_user_context(user_id: str | None) -> None:
    global _current_user_id
    _current_user_id = user_id


def get_user_context() -> str | None:
    return _current_user_id


_SENSITIVE_PATTERNS = [
    (re.compile(r'(access_token["\s:=]+)[^\s,\}\"]{8,}', re.IGNORECASE), r'\1[REDACTED]'),
    (re.compile(r'(refresh_token["\s:=]+)[^\s,\}\"]{8,}', re.IGNORECASE), r'\1[REDACTED]'),
    (re.compile(r'(password["\s:=]+)[^\s,\}\"]{1,}', re.IGNORECASE), r'\1[REDACTED]'),
    (re.compile(r'(otp[_\s]?code["\s:=]+)[^\s,\}\"]{1,}', re.IGNORECASE), r'\1[REDACTED]'),
    (re.compile(r'(apikey["\s:=]+)[^\s,\}\"]{8,}', re.IGNORECASE), r'\1[REDACTED]'),
    (re.compile(r'(secret["\s:=]+)[^\s,\}\"]{8,}', re.IGNORECASE), r'\1[REDACTED]'),
    (re.compile(r'(Bearer\s+)[A-Za-z0-9\-_\.]{20,}', re.IGNORECASE), r'\1[REDACTED]'),
    (re.compile(r'(eyJ[A-Za-z0-9\-_]{20,}\.[A-Za-z0-9\-_]{20,}\.[A-Za-z0-9\-_]{20,})'), '[JWT_REDACTED]'),
]


def sanitize(text: str) -> str:
    for pattern, replacement in _SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _get_log_dir() -> str:
    env_dir = os.getenv("LOG_DIR")
    if env_dir:
        return env_dir

    if sys.platform == "win32":
        base = Path(os.getenv("LOCALAPPDATA") or os.path.expanduser("~"))
        return str(base / "Synapso" / "logs")

    if getattr(sys, "frozen", False):
        return str(Path.home() / ".local" / "share" / "Synapso" / "logs")

    return str(Path(os.path.dirname(os.path.abspath(sys.argv[0] if sys.argv else __file__))) / "logs")


class _SafeRotatingFileHandler(RotatingFileHandler):
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


class SanitizeFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if record.args:
            try:
                formatted = record.msg % record.args
                record.msg = sanitize(formatted)
                record.args = None
            except (TypeError, ValueError):
                record.msg = sanitize(str(record.msg))
        else:
            record.msg = sanitize(str(record.msg))
        return True


class _ContextFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        record.user_id = _current_user_id or "-"
        return super().format(record)


class _ColorContextFormatter(_ContextFormatter):
    COLORS = {
        logging.DEBUG: "\033[37m",
        logging.INFO: "\033[36m",
        logging.WARNING: "\033[33m",
        logging.ERROR: "\033[31m",
        logging.CRITICAL: "\033[41m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        color = self.COLORS.get(record.levelno, "")
        return f"{color}{msg}{self.RESET}" if color else msg


class _LevelListFilter(logging.Filter):
    def __init__(self, allowed_levels: set[int]):
        super().__init__()
        self.allowed_levels = allowed_levels

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno in self.allowed_levels


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


def _enable_windows_ansi() -> None:
    if sys.platform == "win32":
        try:
            os.system("")
        except Exception:
            pass


_initialized = False


def setup_logging() -> None:
    global _initialized
    if _initialized:
        return
    _initialized = True

    _enable_windows_ansi()

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.handlers.clear()

    log_dir = _get_log_dir()
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "synapso.log")

    file_fmt = _ContextFormatter(
        fmt="%(asctime)s | %(levelname)-8s | %(threadName)s | %(user_id)s | %(name)s.%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    max_bytes = int(os.getenv("LOG_MAX_BYTES", str(5 * 1024 * 1024)))
    backup_count = int(os.getenv("LOG_BACKUP_COUNT", "10"))

    file_handler = _SafeRotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_fmt)
    file_handler.addFilter(SanitizeFilter())

    console_fmt = _ColorContextFormatter(
        fmt="%(asctime)s %(levelname)-8s | %(threadName)s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(console_fmt)
    console_handler.addFilter(SanitizeFilter())

    allowed = _parse_log_levels_env()
    if allowed is not None:
        lvl_filter = _LevelListFilter(allowed)
        file_handler.addFilter(lvl_filter)
        console_handler.addFilter(lvl_filter)

    root.addHandler(file_handler)
    root.addHandler(console_handler)

    for noisy in ("httpx", "httpcore", "hpack", "urllib3", "websockets", "realtime", "gotrue"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str = "synapso") -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)


def get_log_dir() -> str:
    return _get_log_dir()