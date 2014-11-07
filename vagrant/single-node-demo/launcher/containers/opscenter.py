from collections import namedtuple

from .. import ports
from ..runner import run
from ..create_logger import logger


def pull_opscenter(localbuilds=False):
    if not localbuilds:
        run('docker pull datastaxdemos/opscenter')


def launch_opscenter(debug=False, localbuilds=False, cluster_ip=False):
    launch_command = []
    launch_command.append('docker run')

    if debug:
        launch_command.append('-i')
        launch_command.append('-t')
        launch_command.append('--entrypoint /bin/bash')
    else:
        launch_command.append('-d')

    for port in ports.opscenter_ports:
        launch_command.append('-p {0}:{0}'.format(port))

    launch_command.append('--link datastax-enterprise:opscenter')

    if localbuilds:
        launch_command.append('opscenter')
    else:
        launch_command.append('datastaxdemos/opscenter')

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


def configure_agents(container_id, stomp_address):
    run('docker exec %s '
        'sed -i '
        '-e "s|stomp_interface:.*|stomp_interface: %s|g" '
        '/var/lib/datastax-agent/conf/address.yaml' % (
            container_id, stomp_address))

    # this should work, but there may exist a bug
    run('docker exec %s service datastax-agent restart' % container_id)

    # possible workaround
    # run('docker exec %s pkill java' % container_id)
    # run('docker exec %s service dse start' % container_id)
    # run('docker exec %s service datastax-agent start' % container_id)
