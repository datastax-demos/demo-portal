from flask import Blueprint, session, render_template, redirect, request, \
    url_for, current_app

topright_api = Blueprint('topright_api', __name__)


@topright_api.route('/overview')
def overview():
    if 'email' not in session:
        return redirect(url_for('login'))
    access_logger = current_app.cluster.get_access_logger(request,
                                                          session['email'],
                                                          init_log=False)

    return render_template('overview.jinja2')


@topright_api.route('/history')
def history():
    if 'email' not in session:
        return redirect(url_for('login'))
    access_logger = current_app.cluster.get_access_logger(request,
                                                          session['email'],
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
