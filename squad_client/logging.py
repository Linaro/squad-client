import logging
import os


DEBUG = logging.DEBUG
ERROR = logging.ERROR
INFO = logging.INFO
levels_str = {'DEBUG': DEBUG, 'ERROR': ERROR, 'INFO': INFO, None: None}


level_env = os.getenv('LOG_LEVEL')
if level_env not in levels_str:
    level_env = None
level_env = levels_str[level_env]


_level = level_env or INFO
_loggers = []


def getLogger(name=None):
    logger = logging.getLogger(name) if name else logging.getLogger()
    logger.setLevel(_level)

    formatter = logging.Formatter('[%(levelname)s] %(name)s: %(message)s')
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    _loggers.append(logger)

    return logger


def setLevel(level):
    _level = level
    for logger in _loggers:
        logger.setLevel(_level)
