import os

from flask import Flask, request, render_template, session, redirect, url_for, \
    jsonify, flash, make_response
from flask.ext.mail import Mail, Message

from logic import auth, ec2, ctoolutils
from logic.logger import logger

app = Flask(__name__)
app.config.from_pyfile('web-gui.cfg')
mail = Mail(app)


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
    reservation_ids = request.form['reservation-ids']

    for reservation_id in reservation_ids.split(','):
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


@app.route('/overview')
def overview():
    if not 'email' in session:
        return redirect(url_for('login'))

    return render_template('overview.jinja2')


@app.route('/ctool', methods=['GET', 'POST'])
def ctool():
    if not 'email' in session:
        return redirect(url_for('login'))

    # only process form if form has been submitted
    if request.form:
        # make a mutable dict copy
        postvars = request.form.copy().to_dict()

        # for debug purposes
        # flash(request.form)
        # flash(postvars)

        # ensure jQuery doesn't fail
        if not postvars['clustername']:
            flash('Clustername must be set', 'error')
            return render_template('ctool.jinja2')

        postvars = ctoolutils.process(postvars, session)

        # ensure jQuery doesn't fail
        if postvars['num_nodes'] < 1:
            flash('Must launch at least one node', 'error')
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
    if request.method == 'POST':
        vars = request.form
    else:
        vars = request.args

    pem_file = ctoolutils.pemfile(vars)

    if request.method == 'GET' and not pem_file.stdout \
            or 'error' in pem_file.stdout:
        flash('Key not found: %s' % str(pem_file), 'error')
        return redirect('/')

    response = make_response(pem_file.stdout)
    response.headers[
        'Content-Disposition'] = 'attachment; filename=%s.pem' % vars[
        'cluster-id']
    return response


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
        body = 'Your email and password is: {0} / {1}\n\n' \
               'Feel free to bookmark this personalized address: ' \
               'http://demos.datastax.com:5000/login?email={0}'
        body = body.format(safe_email, password)
        msg = Message(subject='DataStax Demo Launcher Authentication',
                      recipients=[safe_email],
                      body=body)
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

    # create new ordering in the form of "timestamp_clustername": instance_data
    processed_data = {}
    for reservation in instance_data:
        for instance in instance_data[reservation]:
            try:
                launch_time = instance_data[reservation][instance]['tags'] \
                    ['launch_time']
                name = instance_data[reservation][instance]['tags']['Name']

                cluster_key = '%s_%s' % (launch_time, name)
                if not cluster_key in processed_data:
                    processed_data[cluster_key] = []

                processed_data[cluster_key].append(
                    instance_data[reservation][instance])
            except:
                continue

    return jsonify(**processed_data)


@app.route('/launch', methods=['POST'])
def launch():
    if not 'email' in session:
        return redirect(url_for('login'))

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

    # flash('Executing: %s' % ' '.join(command[4:]))
    flash('Launching new demo: %s.' % demo)
    logger.info('Executing: %s', ' '.join(command))
    os.system(' '.join(command))

    return redirect(url_for('index'))


@app.route('/kill/<reservationids>')
def kill(reservationids):
    if not 'email' in session:
        return redirect(url_for('login'))

    success = False
    failure = False
    for reservationid in reservationids.split(','):
        result = ec2.kill_reservation(reservationid)

        if result:
            success = True
        else:
            failure = True

    if success:
        flash('One or more instances terminated successfully.', 'success')
    if failure:
        flash('One or more instances termination may not have succeeded.',
              'warn')

    return redirect(url_for('index'))


@app.route('/logout')
def logout():
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
                threaded=True)
