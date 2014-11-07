from collections import namedtuple

from .. import ports
from ..runner import run
from ..create_logger import logger


def pull_coffice(localbuilds=False):
    if not localbuilds:
        run('docker pull datastaxdemos/connected-office &')


def launch_connected_office(debug=False, localbuilds=False, cluster_ip=False):
    launch_command = []
    launch_command.append('docker run')

    if debug:
        launch_command.append('-i')
        launch_command.append('-t')
        launch_command.append('--entrypoint /bin/bash')
    else:
        launch_command.append('-d')

    for port in ports.connected_office_ports:
        launch_command.append('-p {0}:{0}'.format(port))

    launch_command.append('--link datastax-enterprise:connected-office')

    if localbuilds:
        launch_command.append('connected-office')
    else:
        launch_command.append('datastaxdemos/connected-office')

    if cluster_ip:
        launch_command.append(cluster_ip)

    launch_command = ' '.join(launch_command)

    if debug:
        print 'Manually run:'
        print launch_command
    else:
        response = run(launch_command)

        if response.stderr:
            logger.error(response)
        else:
            Response = namedtuple('Response', 'container_id ip')
            container_id = response.stdout
            ip = run('docker exec %s hostname -i' % container_id).stdout
            return Response(container_id, ip)
