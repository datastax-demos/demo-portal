import os

from flask import Blueprint, session, render_template, redirect, url_for, \
    request, jsonify, current_app

from DemoPortalFlask.logic import ec2, ctoolutils

from DemoPortalFlask.logic.common import top_level_directory
from DemoPortalFlask.logic.logger import logger
from DemoPortalFlask.logic.message import msg

dashboard_api = Blueprint('dashboard_api', __name__)

APP_PORTS = {
    'connected-office': 3000,
    'weather-sensors': 3000,
}

# set this for ctool
os.environ['AWS_ACCESS_KEY'] = os.environ['DEMO_AWS_ACCESS_KEY']
os.environ['AWS_SECRET_KEY'] = os.environ['DEMO_AWS_SECRET_KEY']



@dashboard_api.route('/')
def index():
    if 'email' not in session:
        return redirect(url_for('authentication_api.login'))

    return render_template('dashboard.jinja2')


@dashboard_api.route('/server-information')
def server_information():
    if 'email' not in session:
        return redirect(url_for('authentication_api.login'))

    instance_data = ec2.owned_instances(session['email'],
                                        admin=session['admin'])

    # create new ordering in the form of "timestamp_clustername": instance_data
    processed_data = {}
    for reservation in instance_data:
        for instance in instance_data[reservation]:
            try:
                launch_time = instance_data[reservation][instance]['tags'][
                    'launch_time']
                name = instance_data[reservation][instance]['tags']['Name']

                cluster_key = '%s_%s' % (launch_time, name)
                if cluster_key not in processed_data:
                    processed_data[cluster_key] = []

                processed_data[cluster_key].append(
                    instance_data[reservation][instance])
            except:
                continue

    return jsonify(**processed_data)


@dashboard_api.route('/launch', methods=['POST'])
def launch():
    if 'email' not in session:
        return redirect(url_for('authentication_api.login'))
    access_logger = current_app.cluster.get_access_logger(request,
                                                          session['email'])
    access_logger.launch(request.form['demoChoice'])

    demo = request.form['demoChoice'].lower().replace(' ', '-')
    command = [
        'DEMO_AWS_ACCESS_KEY=%s' % os.environ['DEMO_AWS_ACCESS_KEY'],
        'DEMO_AWS_SECRET_KEY=%s' % os.environ['DEMO_AWS_SECRET_KEY'],
        'USER_EMAIL=%s' % session['email'],
        'DEMO=%s' % demo,
        'TTL=%s' % request.form['ttl'],
        'PORT=%s' % APP_PORTS[demo],
        'SIZE=%s' % request.form['clustersize'],
        'MODE=-k',
        '%s/vagrant/multi-node-demo/new-cluster' % top_level_directory,
        '&'
    ]

    msg(access_logger, ' '.join(command[4:]), 'debug')
    msg(access_logger, 'Launching new demo: %s.' % demo)
    logger.info('Executing: %s', ' '.join(command))
    os.system(' '.join(command))

    return redirect(url_for('dashboard_api.index'))


@dashboard_api.route('/ctool', methods=['GET', 'POST'])
def ctool():
    if 'email' not in session:
        return redirect(url_for('authentication_api.login'))
    access_logger = current_app.cluster.get_access_logger(request,
                                                          session['email'])

    # only process form if form has been submitted
    if request.form:
        access_logger.launch('ctool')

        # make a mutable dict copy
        postvars = request.form.copy().to_dict()

        # ensure jQuery doesn't fail
        if not postvars['clustername']:
            msg(access_logger, 'Clustername must be set', 'error')
            return render_template('ctool.jinja2')

        postvars = ctoolutils.process(postvars, session)

        # ensure jQuery doesn't fail
        if postvars['num_nodes'] < 1:
            msg(access_logger, 'Must launch at least one node', 'error')
            return render_template('ctool.jinja2')

        try:
            response = ctoolutils.launch(postvars)
            if response:
                return render_template(
                    ctoolutils.error_handling(response, postvars, 'launch'))

            reservation_id = ec2.find_reservation_id_by_tag('cluster_name',
                                                            postvars[
                                                                'full_name'])

            response = ctoolutils.install(postvars, reservation_id)
            if response:
                return render_template(
                    ctoolutils.error_handling(response, postvars, 'install'))

            response = ctoolutils.install_opscenter(postvars, reservation_id)
            if response:
                return render_template(
                    ctoolutils.error_handling(response, postvars, 'install'))

            response = ctoolutils.start(postvars, reservation_id)
            if response:
                return render_template(
                    ctoolutils.error_handling(response, postvars, 'start'))

            response = ctoolutils.start_opscenter(postvars, reservation_id)
            if response:
                return render_template(
                    ctoolutils.error_handling(response, postvars, 'start'))

            response = ctoolutils.start_agent(postvars, reservation_id)
            if response:
                return render_template(
                    ctoolutils.error_handling(response, postvars, 'start'))

            ec2.tag_reservation(reservation_id, 'status', 'Complete.')
            return redirect('/')
        except:
            logger.exception('Exception seen on /ctool:')
            return render_template(
                ctoolutils.error_handling('Logic exception.',
                                          postvars, '/ctool'))

    return render_template('ctool.jinja2')


@dashboard_api.route('/kill')
def kill():
    if 'email' not in session:
        return redirect(url_for('authentication_api.login'))
    access_logger = current_app.cluster.get_access_logger(request,
                                                          session['email'])

    reservation_ids = request.args['reservation_ids']

    success = False
    failure = False
    for reservation_id in reservation_ids.split(','):
        result = ec2.kill_reservation(reservation_id)

        if result:
            success = True
        else:
            failure = True

    if success:
        msg(access_logger, 'Instance(s) terminated successfully.',
            'success')
    if failure:
        msg(access_logger, 'Instance termination(s) may not have succeeded.',
            'warn')

    return redirect(url_for('dashboard_api.index'))


@dashboard_api.route('/ttl', methods=['POST'])
def ttl():
    if 'email' not in session:
        return redirect(url_for('authentication_api.login'))
    access_logger = current_app.cluster.get_access_logger(request,
                                                          session['email'])

    request_ttl = int(request.form['ttl'])
    reservation_ids = request.form['reservation-ids']

    for reservation_id in reservation_ids.split(','):
        ec2.tag_reservation(reservation_id, 'ttl', request_ttl)

    msg(access_logger, 'TTL updated to %s.' % request_ttl)
    return redirect(url_for('dashboard_api.index'))
