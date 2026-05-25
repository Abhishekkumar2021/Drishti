"""Unit tests for structured logging setup."""

from __future__ import annotations

import pytest

from drishti.observability.logging import configure_structured_logging, get_logger


@pytest.mark.unit
def test_configure_structured_logging_idempotent() -> None:
    configure_structured_logging(level="INFO", json_logs=False)
    configure_structured_logging(level="INFO", json_logs=False)
    logger = get_logger("test")
    logger.info("structured_log_test", status="ok")
