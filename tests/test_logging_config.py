"""测试日志配置。"""

import logging
from pathlib import Path

from ecom_agent.agent.telemetry import log_model_call
from ecom_agent.logging_config import setup_logging


def test_setup_logging_writes_utf8_log(
    tmp_path: Path,
) -> None:
    """日志应该写入 UTF-8 文件。"""

    log_file = tmp_path / "agent.log"
    logger = logging.getLogger("ecom_agent")

    try:
        setup_logging(log_file)
        log_model_call(
            tool_names=["search_policy"],
            elapsed_ms=12.34,
        )

        for handler in logger.handlers:
            handler.flush()

        content = log_file.read_text(
            encoding="utf-8"
        )

        assert "model_call" in content
        assert "search_policy" in content
        assert "12.34" in content
    finally:
        for handler in list(logger.handlers):
            if not isinstance(
                handler,
                logging.handlers.RotatingFileHandler,
            ):
                continue

            if Path(handler.baseFilename).resolve() != log_file.resolve():
                continue

            logger.removeHandler(handler)
            handler.close()


def test_setup_logging_does_not_duplicate_handler(
    tmp_path: Path,
) -> None:
    """重复配置日志时不应该添加重复处理器。"""

    log_file = tmp_path / "agent.log"
    logger = logging.getLogger("ecom_agent")

    try:
        setup_logging(log_file)
        setup_logging(log_file)

        matching_handlers = [
            handler
            for handler in logger.handlers
            if isinstance(
                handler,
                logging.handlers.RotatingFileHandler,
            )
            and Path(handler.baseFilename).resolve()
            == log_file.resolve()
        ]

        assert len(matching_handlers) == 1
    finally:
        for handler in list(logger.handlers):
            if not isinstance(
                handler,
                logging.handlers.RotatingFileHandler,
            ):
                continue

            if Path(handler.baseFilename).resolve() != log_file.resolve():
                continue

            logger.removeHandler(handler)
            handler.close()