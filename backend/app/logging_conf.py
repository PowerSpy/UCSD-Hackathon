"""Configure stdlib logging from settings (call once at app startup)."""

import logging

from app.config import settings


def setup_logging() -> None:
    level = getattr(logging, (settings.log_level or "INFO").upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
