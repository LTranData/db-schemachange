from contextlib import contextmanager
from pathlib import Path
from unittest.mock import Mock

import structlog

TEST_DIR = Path(__file__).parent.resolve()


@contextmanager
def mock_structlog_logger():
    original_get_logger = structlog.get_logger
    mock_logger = Mock(spec=structlog.BoundLogger)
    mock_logger.debug = Mock()
    mock_logger.info = Mock()
    mock_logger.warning = Mock()
    mock_logger.error = Mock()
    mock_logger.critical = Mock()

    try:
        structlog.get_logger = lambda *args, **kwargs: mock_logger
        yield mock_logger
    finally:
        structlog.get_logger = original_get_logger
