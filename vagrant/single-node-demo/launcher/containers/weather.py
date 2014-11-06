from collections import namedtuple

from .. import ports
from ..runner import run
from ..create_logger import logger


def launch_weather_sensors(debug=False, localbuilds=False, cluster_ip=False):
    if not localbuilds:
        run('docker pull datastaxdemos/weather-sensors')

    launch_command = []
    launch_command.append('docker run')

    if debug:
        launch_command.append('-i')
        launch_command.append('-t')
        launch_command.append('--entrypoint /bin/bash')
    else:
        launch_command.append('-d')

    for port in ports.weather_sensors_ports:
        launch_command.append('-p {0}:{0}'.format(port))

    launch_command.append('--link datastax-enterprise:weather-sensors')

    if localbuilds:
        launch_command.append('weather-sensors')
    else:
        launch_command.append('datastaxdemos/weather-sensors')

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

