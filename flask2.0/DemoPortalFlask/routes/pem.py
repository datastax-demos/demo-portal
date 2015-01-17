from flask import Blueprint, session, redirect, url_for, request, \
    render_template, make_response, current_app

from DemoPortalFlask.logic import ctoolutils
from DemoPortalFlask.logic.common import top_level_directory
from DemoPortalFlask.logic.message import msg

pem_api = Blueprint('pem_api', __name__)


@pem_api.route('/pem')
def pem():
    if 'email' not in session:
        return redirect(url_for('authentication_api.login'))
    access_logger = current_app.cluster.get_access_logger(request,
                                                          session['email'],
                                                          init_log=False)

    pem_file = open(
        '%s/vagrant/keys/default-user.key' % top_level_directory).read()
    return render_template('pem.jinja2',
                           pem_file=pem_file)


@pem_api.route('/defaultpem')
def defaultpem():
    if 'email' not in session:
        return redirect(url_for('authentication_api.login'))
    access_logger = current_app.cluster.get_access_logger(request,
                                                          session['email'])

    pem_file = open(
        '%s/vagrant/keys/default-user.key' % top_level_directory).read()

    response = make_response(pem_file)
    response.headers['Content-Disposition'] = 'attachment; ' \
                                              'filename=demo-launcher.pem'
    return response


@pem_api.route('/pemfile', methods=['GET', 'POST'])
def pemfile():
    user = session['email'] if 'email' in session else 'Unauthenticated User'
    access_logger = current_app.cluster.get_access_logger(request, user)
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
