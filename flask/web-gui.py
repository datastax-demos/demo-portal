import datetime
import os

from flask import Flask, request, render_template, session, redirect, url_for, \
    jsonify, flash, make_response
from flask.ext.mail import Mail, Message

from logic import auth, ec2, ctoolutils
from logic.cassandracluster import CassandraCluster
from logic.logger import logger

app = Flask(__name__)
app.config.from_pyfile('web-gui.cfg')
mail = Mail(app)

cluster = CassandraCluster(app)

APP_PORTS = {
    'connected-office': 3000,
    'weather-sensors': 3000,
}

top_level_directory = os.path.dirname(
    os.path.dirname(os.path.realpath(__file__)))


def msg(access_logger, message, level='info', log=True):
    if level != 'debug':
        flash(message, level)
    if log:
        access_logger.update(level, message)


@app.route('/')
def index():
    if 'email' not in session:
        return redirect(url_for('login'))

    return render_template('dashboard.jinja2')


@app.route('/ttl', methods=['POST'])
def ttl():
    if 'email' not in session:
        return redirect(url_for('login'))
    access_logger = cluster.get_access_logger(request, session['email'])

    request_ttl = int(request.form['ttl'])
    reservation_ids = request.form['reservation-ids']

    for reservation_id in reservation_ids.split(','):
        ec2.tag_reservation(reservation_id, 'ttl', request_ttl)

    msg(access_logger, 'TTL updated to %s.' % request_ttl)
    return redirect(url_for('index'))


@app.route('/pem')
def pem():
    if 'email' not in session:
        return redirect(url_for('login'))
    access_logger = cluster.get_access_logger(request, session['email'],
                                              init_log=False)

    pem_file = open(
        '%s/vagrant/keys/default-user.key' % top_level_directory).read()
    return render_template('pem.jinja2',
                           pem_file=pem_file)


@app.route('/defaultpem')
def defaultpem():
    if 'email' not in session:
        return redirect(url_for('login'))
    access_logger = cluster.get_access_logger(request, session['email'])

    pem_file = open(
        '%s/vagrant/keys/default-user.key' % top_level_directory).read()

    response = make_response(pem_file)
    response.headers['Content-Disposition'] = 'attachment; ' \
                                              'filename=demo-launcher.pem'
    return response


@app.route('/overview')
def overview():
    if 'email' not in session:
        return redirect(url_for('login'))
    access_logger = cluster.get_access_logger(request, session['email'],
                                              init_log=False)

    return render_template('overview.jinja2')


@app.route('/ctool', methods=['GET', 'POST'])
def ctool():
    if 'email' not in session:
        return redirect(url_for('login'))
    access_logger = cluster.get_access_logger(request, session['email'])

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


@app.route('/pemfile', methods=['GET', 'POST'])
def pemfile():
    user = session['email'] if 'email' in session else 'Unauthenticated User'
    access_logger = cluster.get_access_logger(request, user)
    if request.method == 'POST':
        request_vars = request.form
    else:
        request_vars = request.args

    pem_file = ctoolutils.pemfile(request_vars)

    if request.method == 'GET' and not pem_file.stdout \
            or 'error' in pem_file.stdout:
        msg(access_logger, 'Key not found: %s' % str(pem_file), 'error')
        return redirect('/')

    response = make_response(pem_file.stdout)
    response.headers['Content-Disposition'] = 'attachment; filename=%s.pem' % \
                                              request_vars['cluster-id']
    return response


@app.route('/login', methods=['GET', 'POST'])
def login():
    access_logger = cluster.get_access_logger(request)
    if request.method == 'POST':
        user_record = cluster.get_user(request.form['email'])
        password_hash = auth.hash(request.form['password'], app.secret_key)

        logger.info('login-full:' + request.form['password'])
        logger.info('login-hash:' + auth.hash(request.form['password'], app.secret_key))

        if user_record and user_record[0]['password_hash'] == password_hash:
            msg(access_logger, 'Login successful.', 'debug')
            session['email'] = request.form['email']
            session['admin'] = user_record[0]['admin']
            return redirect(url_for('index'))
        else:
            msg(access_logger, 'Authentication failed.', 'error')
            return render_template('login.jinja2')
    else:
        return render_template('login.jinja2')


@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if 'email' not in session:
        return redirect(url_for('login'))
    access_logger = cluster.get_access_logger(request, session['email'])

    if request.method == 'POST':
        if request.form['new-password'] != request.form['confirm-password']:
            msg(access_logger, 'New passwords did not match.', 'error')
            return render_template('change-password.jinja2')

        user_record = cluster.get_user(session['email'])
        password_hash = auth.hash(request.form['current-password'],
                                  app.secret_key)

        if user_record and user_record[0]['password_hash'] == password_hash:
            cluster.set_password(session['email'],
                                 auth.hash(request.form['new-password'],
                                           app.secret_key))
            msg(access_logger, 'Password has been updated.', 'success')
            return render_template('change-password.jinja2')

        else:
            msg(access_logger, 'Current password did not match.', 'error')
            return render_template('change-password.jinja2')

    return render_template('change-password.jinja2')


@app.route('/request-password', methods=['GET', 'POST'])
def request_password():
    access_logger = cluster.get_access_logger(request)
    if request.method == 'POST':
        safe_email = False
        try:
            safe_email = auth.is_valid_domain(request.form['email'],
                                              'datastax.com')

            if not safe_email:
                user_record = cluster.get_user(request.form['email'])
                if user_record and \
                                user_record[0]['user'] == request.form['email']:
                    safe_email = user_record[0]['user']
        except:
            logger.exception('Email deemed unsafe!')
        if not safe_email:
            msg(access_logger, 'Error occurred when validating email address. '
                               'Please contact administrator.', 'error')
            return render_template('login.jinja2')

        password = auth.create_new_password()
        cluster.set_password(safe_email, auth.hash(password, app.secret_key))

        logger.info('login-full:' + password)
        logger.info('login-hash:' + auth.hash(password, app.secret_key))

        body = 'Your email and password is: {0} / {1}\n\n' \
               'Feel free to bookmark this personalized address: ' \
               'http://demos.datastax.com:5000/login?email={0}'
        body = body.format(safe_email, password)
        message = Message(subject='DataStax Demo Portal Authentication',
                          recipients=[safe_email],
                          body=body)
        try:
            mail.send(message)
        except:
            logger.exception('Error sending email.')
            msg(access_logger, 'Error occurred when sending email. '
                               'Please contact administrator.', 'error')
            return render_template('login.jinja2')

        msg(access_logger, 'Password emailed.')
        return redirect('%s?email=%s' % (url_for('login'), safe_email))
    else:
        return render_template('login.jinja2')


@app.route('/server-information')
def server_information():
    if 'email' not in session:
        return redirect(url_for('login'))

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


@app.route('/launch', methods=['POST'])
def launch():
    if 'email' not in session:
        return redirect(url_for('login'))
    access_logger = cluster.get_access_logger(request, session['email'])
    access_logger.launch(request.form['demoChoice'])

    demo = request.form['demoChoice'].lower().replace(' ', '-')
    command = [
        'AWS_ACCESS_KEY=%s' % os.environ['AWS_ACCESS_KEY'],
        'AWS_SECRET_KEY=%s' % os.environ['AWS_SECRET_KEY'],
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

    return redirect(url_for('index'))


@app.route('/kill')
def kill():
    if 'email' not in session:
        return redirect(url_for('login'))
    access_logger = cluster.get_access_logger(request, session['email'])

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

    return redirect(url_for('index'))


@app.route('/history')
def history():
    if 'email' not in session:
        return redirect(url_for('login'))
    access_logger = cluster.get_access_logger(request, session['email'],
                                              init_log=False)

    history = access_logger.get_user_access_log(session['email'])
    headings = ['method', 'endpoint',
                'level', 'message',
                'form_variables', 'get_variables',
    ]

    if 'advanced' in request.args:
        headings += ['request', 'request_update', ]

    description = '''Views:
        <a href="{0}">Simple</a> |
        <a href="{0}?advanced">Advanced</a>
        '''.format(request.url_rule)

    return render_template('history.jinja2',
                           history_log=True,
                           title='User History',
                           description=description,
                           headings=headings,
                           history=history)


@app.route('/toggle-admin')
def toggle_admin():
    if 'email' not in session:
        return redirect(url_for('login'))
    access_logger = cluster.get_access_logger(request, session['email'])

    user_record = cluster.get_user(session['email'])
    if not user_record or not user_record[0]['admin']:
        msg(access_logger, 'Admin privileges not enabled for this account.',
            'error')
        return redirect(request.referrer)

    if 'admin' not in session:
        session['admin'] = True
        return redirect(request.referrer)
    else:
        del session['admin']

    return redirect(url_for('index'))


@app.route('/admin-history')
@app.route('/admin-history/<int:page>')
def admin_history(page=0):
    if 'email' not in session:
        return redirect(url_for('login'))
    access_logger = cluster.get_access_logger(request, session['email'],
                                              init_log=False)

    if 'admin' not in session:
        msg(access_logger, 'Enable admin privileges first.', 'error')
        return redirect(request.referrer)

    msg(access_logger,
        'This query is expensive. Please do not refresh more than needed.',
        'warn', log=False)

    date = datetime.datetime.combine(datetime.date.today(),
                                     datetime.datetime.min.time())
    date = date + datetime.timedelta(days=-1 * page)

    page_range = 9
    start_range = page - page_range / 2 if (page - page_range / 2) > 0 else 0
    paging = {
        'date': datetime.date.today() + datetime.timedelta(days=-1 * page),
        'page': page,
        'start_range': start_range,
        'end_range': start_range + page_range,
        'back': page - 1 if (page - 1) > 0 else 0,
        'forward': page + 1
    }

    history = access_logger.get_access_log(date)
    headings = ['user',
                'request', 'request_update',
                'method', 'endpoint',
                'level', 'message',
                'form_variables', 'get_variables',
    ]

    return render_template('history.jinja2',
                           history_log=True,
                           title='Admin History',
                           paging=paging,
                           headings=headings,
                           history=history)


@app.route('/last-seen')
def last_seen():
    if 'email' not in session:
        return redirect(url_for('login'))
    access_logger = cluster.get_access_logger(request, session['email'],
                                              init_log=False)

    if 'admin' not in session:
        msg(access_logger, 'Enable admin privileges first.', 'error')
        return redirect(request.referrer)

    history = access_logger.get_last_seen_log()
    headings = ['user', 'date']

    return render_template('history.jinja2',
                           title='Last Seen',
                           headings=headings,
                           history=history)


@app.route('/launches')
def launches():
    if 'email' not in session:
        return redirect(url_for('login'))
    access_logger = cluster.get_access_logger(request, session['email'],
                                              init_log=False)

    if 'admin' not in session:
        msg(access_logger, 'Enable admin privileges first.', 'error')
        return redirect(request.referrer)

    msg(access_logger,
        'This query is expensive. Please do not refresh more than needed.',
        'warn', log=False)

    history = access_logger.get_launches()
    headings = ['date', 'demo', 'user']

    if 'advanced' in request.args:
        headings += ['form_variables', 'request', 'time']

    description = '''Views:
        <a href="{0}">Simple</a> |
        <a href="{0}?advanced">Advanced</a>
        '''.format(request.url_rule)

    return render_template('history.jinja2',
                           title='Launch History (by Date)',
                           description=description,
                           headings=headings,
                           history=history)


@app.route('/demo-launches')
def demo_launches():
    if 'email' not in session:
        return redirect(url_for('login'))
    access_logger = cluster.get_access_logger(request, session['email'],
                                              init_log=False)

    if 'admin' not in session:
        msg(access_logger, 'Enable admin privileges first.', 'error')
        return redirect(request.referrer)

    msg(access_logger,
        'This query is expensive. Please do not refresh more than needed.',
        'warn', log=False)

    history = access_logger.get_demo_launches()
    headings = ['demo', 'user', 'time']

    if 'advanced' in request.args:
        headings += ['form_variables', 'request']

    description = '''Views:
        <a href="{0}">Simple</a> |
        <a href="{0}?advanced">Advanced</a>
        '''.format(request.url_rule)

    return render_template('history.jinja2',
                           title='Launch History (by Demo)',
                           description=description,
                           headings=headings,
                           history=history)


@app.route('/logout')
def logout():
    if 'email' not in session:
        return redirect(url_for('login'))
    access_logger = cluster.get_access_logger(request, session['email'])

    session.pop('email', None)
    return redirect(url_for('index'))


if __name__ == '__main__':
    if app.debug:
        app.run(port=5000,
                use_reloader=True,
                threaded=True)
    else:
        app.run(host='0.0.0.0',
                port=5000,
                use_reloader=True,
                threaded=True)
