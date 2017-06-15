from logging import StreamHandler, Formatter, getLogger, DEBUG
from config.settings import SPARK_APP_NAME

_logger = getLogger(SPARK_APP_NAME)
_configured = None

def get_logger():
    return _logger

def enable(level=DEBUG):
    if _configured:
        return _logger

    _logger.setLevel(level)

    handler = StreamHandler()
    handler.setLevel(level)

    formatter = Formatter("%(name)s - %(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    _logger.addHandler(handler)

    return _logger
