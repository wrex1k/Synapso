"""
Backward-compatible logger module.

All logging infrastructure lives in app.utils.logging_config.
This module re-exports get_logger and provides the default `logger` instance
so existing `from app.utils.logger import logger` imports keep working.
"""

from app.utils.logging_config import get_logger  # noqa: F401

logger = get_logger("synapso")