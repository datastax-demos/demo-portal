from collections import namedtuple

from .. import ports
from ..runner import run
from ..create_logger import logger


def launch_dse(debug=False, localbuilds=False,
               spark=False, solr=False, hadoop=False,
               sharkserver=False, hiveserver=False):
    if not localbuilds:
        run('docker pull datastaxdemos/datastax-enterprise')

    launch_command = []
    launch_command.append('docker run')

    if debug:
        launch_command.append('-i')
        launch_command.append('-t')
        launch_command.append('--entrypoint /bin/bash')
    else:
        launch_command.append('-d')

    launch_command.append('-v /mnt/cassandra:/var/lib/cassandra')

    for port in ports.dse_ports:
        launch_command.append('-p {0}:{0}'.format(port))

    launch_command.append('--name datastax-enterprise')

    if localbuilds:
        launch_command.append('datastax-enterprise')
    else:
        launch_command.append('datastaxdemos/datastax-enterprise')

    if not debug:
        if spark:
            launch_command.append('-k')
        if solr:
            launch_command.append('-s')
        if hadoop:
            launch_command.append('-t')

        if sharkserver:
            launch_command.append('--sharkserver 5588')
        if hiveserver:
            launch_command.append('--hiveserver 5587')

    launch_command = ' '.join(launch_command)

    if debug:
        print 'Manually run:'
        print launch_command
    else:
        response = run(launch_command)

        if response.stderr:
            logger.error(response)
            return response
        else:
            Response = namedtuple('Response', 'container_id ip')
            container_id = response.stdout
            ip = run('docker exec %s hostname -i' % container_id).stdout
            return Response(container_id, ip)
