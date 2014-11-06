import logging

LOGGER_NAME = 'cleanup'

logger = logging.getLogger(LOGGER_NAME)
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('/mnt/logs/%s.log' % LOGGER_NAME)
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)
