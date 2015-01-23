import datetime

from flask import Blueprint, url_for, session, render_template, request, \
    redirect, current_app

from DemoPortalFlask.logic.message import msg

admin_api = Blueprint('admin_api', __name__)


@admin_api.route('/toggle-admin')
def toggle_admin():
    if 'email' not in session:
        return redirect(url_for('authentication_api.login'))
    access_logger = current_app.cluster.get_access_logger(request,
                                                          session['email'])

    user_record = current_app.cluster.get_user(session['email'])
    if not user_record or not user_record[0]['admin']:
        msg(access_logger, 'Admin privileges not enabled for this account.',
            'error')
        return redirect(request.referrer)

    if 'admin' not in session:
        session['admin'] = True
        return redirect(request.referrer)
    else:
        del session['admin']

    return redirect(url_for('dashboard_api.index'))


@admin_api.route('/admin-history')
@admin_api.route('/admin-history/<int:page>')
def admin_history(page=0):
    if 'email' not in session:
        return redirect(url_for('authentication_api.login'))
    access_logger = current_app.cluster.get_access_logger(request,
                                                          session['email'],
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


@admin_api.route('/last-seen')
def last_seen():
    if 'email' not in session:
        return redirect(url_for('authentication_api.login'))
    access_logger = current_app.cluster.get_access_logger(request,
                                                          session['email'],
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


@admin_api.route('/launches')
def launches():
    if 'email' not in session:
        return redirect(url_for('authentication_api.login'))
    access_logger = current_app.cluster.get_access_logger(request,
                                                          session['email'],
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


@admin_api.route('/demo-launches')
def demo_launches():
    if 'email' not in session:
        return redirect(url_for('authentication_api.login'))
    access_logger = current_app.cluster.get_access_logger(request,
                                                          session['email'],
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
