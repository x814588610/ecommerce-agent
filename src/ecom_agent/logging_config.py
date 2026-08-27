"""配置项目日志输出。"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOG_FILE = PROJECT_ROOT / "logs" / "agent.log"


def setup_logging(
    log_file: Path | None = None,
) -> Path:
    """配置 Agent 日志文件并返回日志路径。"""

    target_file = (
        log_file
        if log_file is not None
        else DEFAULT_LOG_FILE
    )
    target_file = target_file.resolve()
    target_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    logger = logging.getLogger("ecom_agent")
    logger.setLevel(logging.INFO)

    for handler in logger.handlers:
        if not isinstance(handler, RotatingFileHandler):
            continue

        if Path(handler.baseFilename).resolve() == target_file:
            return target_file

    handler = RotatingFileHandler(
        target_file,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s "
            "%(name)s %(message)s"
        )
    )
    logger.addHandler(handler)

    return target_file