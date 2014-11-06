import shlex
import subprocess

from collections import namedtuple
from create_logger import logger

def run(command):
    logger.info('Running: %s' % command)
    Response = namedtuple('Response', 'command stdout stderr')
    process = subprocess.Popen(shlex.split(command),
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    read = process.communicate()
    return Response(command,
                    read[0].strip(),
                    read[1].strip())
