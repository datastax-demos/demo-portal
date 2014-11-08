import os

from optparse import OptionGroup, OptionParser


def read_options():
    parser = OptionParser()

    group = OptionGroup(parser, 'Demo Options',
                        'Options for which demo to run.')
    group.add_option('--demo',
                     help='choose the Docker container to run')
    group.add_option('--aws-access-key',
                     help='set to allow instance tagging')
    group.add_option('--aws-secret-key',
                     help='set to allow instance tagging')
    parser.add_option_group(group)

    group = OptionGroup(parser, 'Node Type Options',
                        'Set the DSE node type.')
    group.add_option('-k', '--spark',
                     action='store_true', default=False,
                     help='enable the Spark service')
    group.add_option('-s', '--solr',
                     action='store_true', default=False,
                     help='enable the Solr service')
    group.add_option('-t', '--hadoop',
                     action='store_true', default=False,
                     help='enable the Hadoop (Task Tracker) service')
    parser.add_option_group(group)

    group = OptionGroup(parser, 'Docker Options',
                        'Setup the docker environment.')
    group.add_option('--localbuilds',
                     action='store_true', default=False,
                     help='use local docker builds')
    group.add_option('--debug',
                     action='store_true', default=False,
                     help='print debug information')
    parser.add_option_group(group)

    (options, args) = parser.parse_args()

    # set for later use
    os.environ['AWS_ACCESS_KEY'] = options.aws_access_key
    os.environ['AWS_SECRET_KEY'] = options.aws_secret_key

    return options

options = read_options()
