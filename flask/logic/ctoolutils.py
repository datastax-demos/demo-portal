import re
from tempfile import NamedTemporaryFile
import time
from flask import flash
import json

import execute, ec2
from logger import logger

whitespace_strip = re.compile('\s')
alphanumeric_strip = re.compile('\W+')


def error_handling(response, postvars, state):
    # tag the instances appropriately
    reservation_id = ec2.find_reservation_id_by_tag('cluster_name',
                                                    postvars['full_name'])
    ec2.tag_reservation(reservation_id, 'status',
                        'Failure seen on startup. Discard cluster.')

    # alert the user by flash message
    flash('Error seen on %s: %s' % (state, str(response)), 'error')
    return 'ctool.jinja2'

def process(postvars, session):
    # format the cluster_name and email as ctool will see it
    postvars['clustername'] = re.sub(whitespace_strip, '_',
                                     postvars['clustername'])
    postvars['clustername'] = re.sub(alphanumeric_strip, '',
                                     postvars['clustername'])
    postvars['full_name'] = '%s_%s_%s' % (session['email'],
                                          postvars['clustername'],
                                          time.time())
    postvars['full_name'] = re.sub(alphanumeric_strip, '',
                                   postvars['full_name'])
    postvars['clean_email'] = re.sub(alphanumeric_strip, '', session['email'])
    postvars['log_file'] = '%s_%s.log' % (time.time(),
                                          postvars['clustername'])

    # calculate ttl
    postvars['ttl'] = (int(postvars['ttl-days']) * 24 +
                       int(postvars['ttl-hours']))

    # create tags
    postvars['tags'] = {
        'status': 'Initializing...',
        'ctool_name': postvars['clustername'],
        'provisioner': 'demo-portal-launcher',
        'email': session['email'],
        'launch_time': int(time.time()),
        'ttl': postvars['ttl']
    }
    postvars['tags'] = json.dumps(postvars['tags'])

    # calculate the number of nodes requested
    postvars['num_nodes'] = int(postvars['cassandra-nodes']) + \
                            int(postvars['hadoop-nodes']) + \
                            int(postvars['search-nodes']) + \
                            int(postvars['spark-nodes'])

    # create skeleton for advanced topology
    postvars['advanced_nodes'] = {
        'cluster': {
            'snitch': 'PropertyFileSnitch',
            'nodes': {}
        }
    }

    # configure advanced topology, if used
    if 'dc1-name' in postvars:
        postvars['num_nodes'] = 0
        for i in range(5):
            dc = 'dc%s' % (i + 1)
            name = postvars['%s-name' % dc]

            for j in range(10):
                node_type = postvars['%s-node%s' % (dc, j)]

                if node_type != 'null':
                    postvars['advanced_nodes']['cluster']['nodes'][
                        postvars['num_nodes']] = {
                        'datacenter': name,
                        'rack': 'rack1',
                        'node_type': node_type
                    }

                    postvars['num_nodes'] += 1

    return postvars


def launch(postvars):
    # TODO: Use automaton library, not command line
    # currently chose shell commands to teach presales ctool in a more
    # relatable fashion
    launch_command = 'ctool' \
                     ' --log-dir automaton_logs/%(clean_email)s' \
                     ' --log-file %(log_file)s' \
                     ' --provider %(cloud-option)s' \
                     ' launch' \
                     ' --instance-type %(instance-type)s' \
                     ' --platform %(platform)s' \
                     ' --tags \'%(tags)s\'' \
                     ' %(full_name)s' \
                     ' %(num_nodes)s'
    launch_command = launch_command % postvars
    flash(launch_command)

    logger.info('Executing: %s', launch_command)
    response = execute.run(launch_command)

    if response.stderr:
        return response


def install(postvars, reservation_id):
    ec2.tag_reservation(reservation_id, 'user', remove=True)
    ec2.tag_reservation(reservation_id, 'status',
                        'Installing %(product-name)s...' % postvars)

    postvars['spark_hadoop'] = '--spark-hadoop' \
        if 'spark-and-hadoop' in postvars else ''

    if len(postvars['advanced_nodes']['cluster']['nodes']) == 0:
        # calculate install values
        postvars['percent_analytics'] = float(postvars['hadoop-nodes']) / \
                                        postvars['num_nodes']
        postvars['percent_search'] = float(postvars['search-nodes']) / \
                                     postvars['num_nodes']
        postvars['percent_spark'] = float(postvars['spark-nodes']) / \
                                    postvars['num_nodes']

        install_command = 'ctool ' \
                          ' --provider %(cloud-option)s' \
                          ' install' \
                          ' --repo staging' \
                          ' --percent-analytics %(percent_analytics)s' \
                          ' --percent-search %(percent_search)s' \
                          ' --percent-spark %(percent_spark)s' \
                          ' %(spark_hadoop)s' \
                          ' --version_or_branch %(dse-version)s' \
                          ' --num-tokens %(num-of-tokens)s' \
                          ' %(full_name)s' \
                          ' %(product-name)s'
        install_command = install_command % postvars

        logger.info('Executing: %s', install_command)
        response = execute.run(install_command)
        flash(install_command)
    else:
        with NamedTemporaryFile() as f:
            postvars['config_file'] = f.name
            f.write(json.dumps(postvars['advanced_nodes'], indent=4,
                               sort_keys=True))
            f.flush()

            install_command = 'ctool' \
                              ' --provider %(cloud-option)s' \
                              ' install' \
                              ' --repo staging' \
                              ' --config-file %(config_file)s' \
                              ' %(spark_hadoop)s' \
                              ' --version_or_branch %(dse-version)s' \
                              ' --num-tokens %(num-of-tokens)s' \
                              ' %(full_name)s' \
                              ' %(product-name)s'
            install_command = install_command % postvars

            logger.info('Executing: %s', install_command)
            logger.debug('With config-file: \n%s', f.read())
            response = execute.run(install_command)

        flash(install_command)
        flash('--config-file: %s' % json.dumps(postvars['advanced_nodes']))

    if response.stderr:
        return response


def install_opscenter(postvars, reservation_id):
    if postvars['opscenter-install'] == 'yes':
        ec2.tag_reservation(reservation_id, 'status', 'Installing opscenter...')
        install_command = 'ctool' \
                          ' --provider %(cloud-option)s' \
                          ' install' \
                          ' --repo staging' \
                          ' --version_or_branch %(opscenter-version)s' \
                          ' %(full_name)s' \
                          ' opscenter'
        install_command = install_command % postvars
        flash(install_command)

        logger.info('Executing: %s', install_command)
        response = execute.run(install_command)

        if response.stderr:
            return response


def start(postvars, reservation_id):
    ec2.tag_reservation(reservation_id, 'status',
                        'Starting %(product-name)s...' % postvars)
    start_command = 'ctool' \
                    ' --provider %(cloud-option)s' \
                    ' start' \
                    ' %(full_name)s' \
                    ' %(product-name)s'
    start_command = start_command % postvars
    flash(start_command)

    logger.info('Executing: %s', start_command)
    response = execute.run(start_command)

    if response.stderr:
        return response


def start_opscenter(postvars, reservation_id):
    if postvars['opscenter-install'] == 'yes':
        ec2.tag_reservation(reservation_id, 'status', 'Starting opscenter...')
        start_command = 'ctool' \
                        ' --provider %(cloud-option)s' \
                        ' start' \
                        ' %(full_name)s' \
                        ' opscenter'
        start_command = start_command % postvars
        flash(start_command)

        logger.info('Executing: %s', start_command)
        response = execute.run(start_command)

        if response.stderr:
            return response


def start_agent(postvars, reservation_id):
    if postvars['opscenter-install'] == 'yes':
        ec2.tag_reservation(reservation_id, 'status',
                            'Starting DataStax Agents...')
        start_command = 'ctool' \
                        ' --provider %(cloud-option)s' \
                        ' run' \
                        ' %(full_name)s' \
                        ' all' \
                        ' "sudo service datastax-agent start"'
        start_command = start_command % postvars
        flash(start_command)

        logger.info('Executing: %s', start_command)
        response = execute.run(start_command)

        if response.stderr:
            return response


def pemfile(request):
    run_command = 'ctool' \
                  ' --provider %(cloud-option)s' \
                  ' dump_key' \
                  ' %(cluster-id)s'
    run_command = run_command % request

    logger.info('Executing: %s', run_command)
    response = execute.run(run_command)
    return response
