import logging
import logging.handlers

LOGGER_NAME = 'cleanup'

logger = logging.getLogger(LOGGER_NAME)
logger.setLevel(logging.DEBUG)
fh = logging.handlers.RotatingFileHandler('/mnt/logs/%s.log' % LOGGER_NAME,
                                          maxBytes=50000000, backupCount=5)
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)
