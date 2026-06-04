import sys
from loguru import logger

def setup_logger():
    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | "
        "<level>{level:<8}</level | >"
        "{message}",
        colorize=True
    )

    logger.add(
        "logs/app.log",
        level="INFO",
        rotation="10 MB",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {message}",
        encoding="utf-8"
    )

    return logger