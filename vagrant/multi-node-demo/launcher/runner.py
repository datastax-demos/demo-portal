import shlex
import subprocess

from collections import namedtuple
from create_logger import logger

def run(command, wait=True, env=None):
    logger.info('Running: %s' % command)
    process = subprocess.Popen(shlex.split(command),
                               env=env,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)

    if not wait:
        Response = namedtuple('Response', 'command process')
        return Response(command, process)

    read = process.communicate()
    Response = namedtuple('Response', 'command stdout stderr')
    return Response(command,
                    read[0].strip(),
                    read[1].strip())
