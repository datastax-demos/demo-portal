from flask import Blueprint, url_for, session, render_template, request, \
    redirect, current_app
from flask.ext.mail import Message

from DemoPortalFlask.logic import auth
from DemoPortalFlask.logic.logger import logger
from DemoPortalFlask.logic.message import msg

authentication_api = Blueprint('authentication_api', __name__)


@authentication_api.route('/login', methods=['GET', 'POST'])
def login():
    access_logger = current_app.cluster.get_access_logger(request)
    if request.method == 'POST':
        user_record = current_app.cluster.get_user(request.form['email'])
        password_hash = auth.hash(request.form['password'],
                                  current_app.secret_key)

        logger.info('login-full:' + request.form['password'])
        logger.info('login-hash:' + auth.hash(request.form['password'],
                                              current_app.secret_key))

        if user_record and user_record[0]['password_hash'] == password_hash:
            msg(access_logger, 'Login successful.', 'debug')
            session['email'] = request.form['email']
            session['admin'] = user_record[0]['admin']
            return redirect(url_for('dashboard_api.index'))
        else:
            msg(access_logger, 'Authentication failed.', 'error')
            return render_template('login.jinja2')
    else:
        return render_template('login.jinja2')


@authentication_api.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if 'email' not in session:
        return redirect(url_for('authentication_api.login'))
    access_logger = current_app.cluster.get_access_logger(request,
                                                          session['email'])

    if request.method == 'POST':
        if request.form['new-password'] != request.form['confirm-password']:
            msg(access_logger, 'New passwords did not match.', 'error')
            return render_template('change-password.jinja2')

        user_record = current_app.cluster.get_user(session['email'])
        password_hash = auth.hash(request.form['current-password'],
                                  current_app.secret_key)

        if user_record and user_record[0]['password_hash'] == password_hash:
            current_app.cluster.set_password(session['email'],
                                             auth.hash(
                                                 request.form['new-password'],
                                                 current_app.secret_key))
            msg(access_logger, 'Password has been updated.', 'success')
            return render_template('change-password.jinja2')

        else:
            msg(access_logger, 'Current password did not match.', 'error')
            return render_template('change-password.jinja2')

    return render_template('change-password.jinja2')


@authentication_api.route('/request-password', methods=['GET', 'POST'])
def request_password():
    access_logger = current_app.cluster.get_access_logger(request)
    if request.method == 'POST':
        safe_email = False
        try:
            safe_email = auth.is_valid_domain(request.form['email'],
                                              'datastax.com')

            if not safe_email:
                user_record = current_app.cluster.get_user(
                    request.form['email'])
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
        current_app.cluster.set_password(safe_email,
                                         auth.hash(password,
                                                   current_app.secret_key))

        logger.info('login-full:' + password)
        logger.info('login-hash:' + auth.hash(password, current_app.secret_key))

        body = 'Your email and password is: {0} / {1}\n\n' \
               'Feel free to bookmark this personalized address: ' \
               'http://demos.datastax.com:5000/login?email={0}'
        body = body.format(safe_email, password)
        message = Message(subject='DataStax Demo Portal Authentication',
                          recipients=[safe_email],
                          body=body)
        try:
            current_app.mail.send(message)
        except:
            logger.exception('Error sending email.')
            msg(access_logger, 'Error occurred when sending email. '
                               'Please contact administrator.', 'error')
            return render_template('login.jinja2')

        msg(access_logger, 'Password emailed.')
        return redirect('%s?email=%s' % (url_for('authentication_api.login'),
                                         safe_email))
    else:
        return render_template('login.jinja2')


@authentication_api.route('/logout')
def logout():
    if 'email' not in session:
        return redirect(url_for('authentication_api.login'))
    access_logger = current_app.cluster.get_access_logger(request,
                                                          session['email'])

    session.pop('email', None)
    return redirect(url_for('dashboard_api.index'))
