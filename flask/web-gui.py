import logging
import os

from flask import Flask, request, render_template, session, redirect, url_for, \
    jsonify, flash
from flask.ext.mail import Mail, Message
import time
import re

from logic import auth, ec2

app = Flask(__name__)
app.config.from_pyfile('web-gui.cfg')
mail = Mail(app)

logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('%s.log' % __file__)
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

APP_PORTS = {
    'connected-office': 3000,
    'weather-sensors': 3000,
}

top_level_directory = os.path.dirname(
    os.path.dirname(os.path.realpath(__file__)))


@app.route('/')
def index():
    if not 'email' in session:
        return redirect(url_for('login'))

    # show all clusters if '?admin' present in url
    session['admin'] = not request.args.get('admin', True)

    return render_template('dashboard.jinja2')


@app.route('/ttl', methods=['POST'])
def ttl():
    if not 'email' in session:
        return redirect(url_for('login'))

    ttl = int(request.form['ttl'])
    reservation_id = request.form['reservation-id']

    ec2.tag_reservation(reservation_id, 'ttl', ttl)
    flash('TTL updated to %s.' % ttl)

    return redirect(url_for('index'))


@app.route('/pem')
def pem():
    if not 'email' in session:
        return redirect(url_for('login'))

    pem_file = open(
        '%s/vagrant/keys/default-user.key' % top_level_directory).read()
    return render_template('pem.jinja2',
                           pem_file=pem_file)


@app.route('/todo')
def todo():
    if not 'email' in session:
        return redirect(url_for('login'))

    return render_template('todo.jinja2')


alphanumeric_strip = re.compile('[\W]+')
@app.route('/ctool', methods=['GET', 'POST'])
def ctool():
    if not 'email' in session:
        return redirect(url_for('login'))

    # only process form if form has been submitted
    if request.form:
        # make a mutable dict copy
        postvars = request.form.copy().to_dict()

        # ensure jQuery doesn't fail
        if not postvars['clustername']:
            flash('Clustername must be set', 'error')
            return render_template('ctool.jinja2')

        # format the cluster_name and email as ctool will see it
        postvars['ctool_name'] = '%s_%s_%s' % (session['email'],
                                               postvars['clustername'],
                                               time.time())
        postvars['ctool_name'] = re.sub(alphanumeric_strip, '', postvars['ctool_name'])
        postvars['clean_email'] = re.sub(alphanumeric_strip, '', session['email'])

        # calculate the number of nodes requested
        postvars['num_nodes'] = int(postvars['cassandra-nodes']) + \
                                int(postvars['hadoop-nodes']) + \
                                int(postvars['search-nodes']) + \
                                int(postvars['spark-nodes'])

        # TODO: Handle advanced setup
        # TODO: Handle TTLs

        # ensure jQuery doesn't fail
        if postvars['num_nodes'] < 1:
            flash('Must launch at least one node', 'error')
            return render_template('ctool.jinja2')

        # TODO: Use automaton library, not command line
        launch_command = 'ctool' \
                         ' --log-dir automaton_logs/%(clean_email)s' \
                         ' --log-file %(ctool_name)s.log' \
                         ' --provider %(cloud-options)s' \
                         ' launch' \
                         ' --instance-type %(instance-type)s' \
                         ' --platform %(platform)s' \
                         ' %(ctool_name)s' \
                         ' %(num_nodes)s'
        launch_command = launch_command % postvars
        flash(launch_command)

        # calculate install values
        postvars['percent_analytics'] = float(postvars['hadoop-nodes']) / postvars['num_nodes']
        postvars['percent_search'] = float(postvars['search-nodes']) / postvars['num_nodes']
        postvars['percent_spark'] = float(postvars['spark-nodes']) / postvars['num_nodes']
        postvars['spark_hadoop'] = '--spark-hadoop' if 'spark-and-hadoop' in postvars else ''

        # TODO: Use automaton library, not command line
        install_command = 'ctool install' \
                          ' --percent-analytics %(percent_analytics)s' \
                          ' --percent-search %(percent_search)s' \
                          ' --percent-hadoop %(percent_spark)s' \
                          ' %(spark_hadoop)s' \
                          ' --version_or_branch %(dse-version)s' \
                          ' --num-tokens %(num-of-tokens)s' \
                          ' %(ctool_name)s' \
                          ' %(product-name)s'
        install_command = install_command % postvars
        flash(install_command)

        if postvars['opscenter-install'] == 'yes':
            # TODO: Use automaton library, not command line
            install_command = 'ctool install' \
                              ' --version_or_branch %(opscenter-version)s' \
                              ' %(ctool_name)s' \
                              ' opscenter'
            install_command = install_command % postvars
            flash(install_command)

    return render_template('ctool.jinja2')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if auth.validate(request.form['email'],
                         request.form['password'],
                         app.secret_key):
            session['email'] = request.form['email']
            return redirect(url_for('index'))
        else:
            flash('Authentication failed.', 'error')
            return render_template('login.jinja2')
    else:
        return render_template('login.jinja2')


@app.route('/request-password', methods=['GET', 'POST'])
def request_password():
    if request.method == 'POST':
        safe_email = False
        try:
            safe_email = auth.validdomain(request.form['email'], 'datastax.com')
        except:
            pass
        if not safe_email:
            flash(
                'Error occurred when validating email address. Please contact '
                'administrator.',
                'error')
            return render_template('login.jinja2')

        password = auth.create(safe_email, app.secret_key)
        msg = Message(subject="DataStax Demo Launcher Authentication",
                      recipients=[safe_email],
                      body="Your email and password is: %s / %s" % (
                          safe_email, password))
        try:
            mail.send(msg)
        except:
            logger.exception('Error sending email.')
            flash(
                'Error occurred when sending email. Please contact '
                'administrator.',
                'error')
            return render_template('login.jinja2')

        flash('Password emailed.', 'info')
        return redirect('%s?email=%s' % (url_for('login'), safe_email))
    else:
        return render_template('login.jinja2')


@app.route('/server-information')
def server_information():
    if not 'email' in session:
        return redirect(url_for('login'))

    instance_data = ec2.owned_instances(session['email'],
                                        admin=session['admin'])
    return jsonify(**instance_data)


@app.route('/launch', methods=['POST'])
def launch():
    if not 'email' in session:
        return redirect(url_for('login'))

    demo = request.form['demoChoice'].lower().replace(' ', '-')
    command = [
        'DATASTAX_USER=%s' % os.environ['DATASTAX_USER'],
        'DATASTAX_PASS=%s' % os.environ['DATASTAX_PASS'],
        'AWS_ACCESS_KEY=%s' % os.environ['AWS_ACCESS_KEY'],
        'AWS_SECRET_KEY=%s' % os.environ['AWS_SECRET_KEY'],
        'USER_EMAIL=%s' % session['email'],
        'DEMO=%s' % demo,
        'TTL=%s' % request.form['ttl'],
        'PORT=%s' % APP_PORTS[demo],
        '%s/vagrant/single-node-demo/new-cluster' % top_level_directory,
        '&'
    ]

    # flash('Executing: %s' % ' '.join(command[4:]))
    flash('Launching new demo: %s.' % demo)
    logger.info('Executing: %s' % ' '.join(command))
    os.system(' '.join(command))

    return redirect(url_for('index'))


@app.route('/kill/<reservationid>')
def kill(reservationid):
    if not 'email' in session:
        return redirect(url_for('login'))

    result = ec2.kill_reservation(reservationid)

    if result:
        flash('Instance terminated successfully.', 'success')
    else:
        flash('Instance termination may not have succeeded.', 'warn')

    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect(url_for('index'))


if __name__ == "__main__":
    if app.debug:
        app.run(port=5000,
                use_reloader=True)
    else:
        app.run(host='0.0.0.0',
                port=5000,
                threaded=True)
