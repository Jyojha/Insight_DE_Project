from logging import StreamHandler, Formatter, getLogger, DEBUG
from config.settings import SPARK_APP_NAME, LOGGING_LEVEL

_logger = None

def configure(logger, level):
    logger.setLevel(level)

    handler = StreamHandler()
    handler.setLevel(level)

    formatter = Formatter("%(name)s - %(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    logger.addHandler(handler)

def get_logger():
    global _logger

    if _logger is None:
        _logger = getLogger(SPARK_APP_NAME)
        configure(_logger, LOGGING_LEVEL)

    return _logger
