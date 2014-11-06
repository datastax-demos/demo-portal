import logging
import os

from flask import Flask, request, render_template, session, redirect, url_for, \
    jsonify, flash
from flask.ext.mail import Mail, Message

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
    'connected_office': 3000,
    'weather_sensors': 3000,
}


@app.route('/')
def index():
    if not 'email' in session:
        return redirect(url_for('login'))

    return render_template('dashboard.jinja2')


@app.route('/pem')
def pem():
    if not 'email' in session:
        return redirect(url_for('login'))

    return render_template('pem.jinja2')


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
        return render_template('login.jinja2')
    else:
        return render_template('login.jinja2')


@app.route('/server-information')
def server_information():
    if not 'email' in session:
        return redirect(url_for('login'))

    instance_data = ec2.owned_instances(session['email'])
    return jsonify(**instance_data)


@app.route('/launch', methods=['POST'])
def launch():
    if not 'email' in session:
        return redirect(url_for('login'))

    demo = request.form['demoChoice'].lower().replace(' ', '-')
    current_directory = os.path.dirname(
        os.path.dirname(os.path.realpath(__file__)))
    command = [
        'DATASTAX_USER=%s' % os.environ['DATASTAX_USER'],
        'DATASTAX_PASS=%s' % os.environ['DATASTAX_PASS'],
        'AWS_ACCESS_KEY=%s' % os.environ['AWS_ACCESS_KEY'],
        'AWS_SECRET_KEY=%s' % os.environ['AWS_SECRET_KEY'],
        'USER_EMAIL=%s' % session['email'],
        'DEMO=%s' % demo,
        'TTL=%s' % request.form['ttl'],
        'PORT=%s' % APP_PORTS[demo],
        '%s/vagrant/single-node-demo/new-cluster' % current_directory,
        '&'
    ]

    flash('Executing: %s' % ' '.join(command[4:]))
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
                port=5000)
