import shlex
import subprocess

from collections import namedtuple


def run(command, wait=True):
    process = subprocess.Popen(shlex.split(command),
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
