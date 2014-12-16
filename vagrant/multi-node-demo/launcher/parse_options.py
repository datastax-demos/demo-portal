import os
import sys

from optparse import OptionGroup, OptionParser


def read_options():
    parser = OptionParser()

    group = OptionGroup(parser, 'Demo Options',
                        'Options for which demo to run.')
    group.add_option('--demo', default='connected-office',
                     help='choose the Docker container to run')
    group.add_option('--ttl', type=int, default=2,
                     help='set cluster ttl [default: %default]')
    parser.add_option_group(group)

    group = OptionGroup(parser, 'DSE Options',
                        'set the cluster size and DSE node type.')
    group.add_option('--size', type=int, default=3,
                     help='number of dse nodes')
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

    (options, args) = parser.parse_args()

    if not os.environ['AWS_ACCESS_KEY'] or not os.environ['AWS_SECRET_KEY']:
        sys.exit('Environment variables'
                 ' AWS_ACCESS_KEY and AWS_SECRET_KEY must be set.')

    return options

options = read_options()
