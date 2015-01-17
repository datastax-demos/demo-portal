from flask import flash


def msg(access_logger, message, level='info', log=True):
    if level != 'debug':
        flash(message, level)
    if log:
        access_logger.update(level, message)
