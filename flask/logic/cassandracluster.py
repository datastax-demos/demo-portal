from datetime import datetime
from uuid import UUID as pyUUID, getnode

from cassandra.cluster import Cluster

from logger import logger


def generate_timeuuid():
    """
    code modified from: http://goo.gl/czeA4P
    """
    dt = datetime.now()

    epoch = datetime(1970, 1, 1, tzinfo=dt.tzinfo)
    offset = epoch.tzinfo.utcoffset(epoch).total_seconds() \
        if epoch.tzinfo else 0
    timestamp = (dt - epoch).total_seconds() - offset

    node = None
    clock_seq = None

    nanoseconds = int(timestamp * 1e9)
    timestamp = int(nanoseconds // 100) + 0x01b21dd213814000

    if clock_seq is None:
        import random

        clock_seq = random.randrange(1 << 14)  # instead of stable storage
    time_low = timestamp & 0xffffffff
    time_mid = (timestamp >> 32) & 0xffff
    time_hi_version = (timestamp >> 48) & 0x0fff
    clock_seq_low = clock_seq & 0xff
    clock_seq_hi_variant = (clock_seq >> 8) & 0x3f
    if node is None:
        node = getnode()
    return pyUUID(fields=(time_low, time_mid, time_hi_version,
                          clock_seq_hi_variant, clock_seq_low, node),
                  version=1)


def _sanatize(input_dict):
    """
    remove sensitive data from being logged
    :param input_dict: dictionary
    :return: sanatized dictionary
    """
    if 'password' in input_dict:
        output = input_dict.copy()
        del output['password']
        return output
    return input_dict


class CassandraCluster():
    def __init__(self, app):
        try:
            # connect to DSE cluster
            self.cluster = Cluster([app.config['DSE_CLUSTER']])
            self.session = self.cluster.connect()

            # ensure schema is created
            self.initialize_schema()

            # prepare access insert statement
            self.access_statement = self.session.prepare('''
                INSERT INTO demo_portal.access_log
                    (user, request, request_update,
                    level, endpoint, method, form_variables, get_variables,
                    message)
                VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''')
        except:
            logger.exception('Database objects not created!')

    def initialize_schema(self):
        self.session.execute('''
            CREATE KEYSPACE IF NOT EXISTS demo_portal
            WITH replication = {'class': 'SimpleStrategy',
                                'replication_factor': 1 }
        ''')

        self.session.execute('''
            CREATE TABLE IF NOT EXISTS demo_portal.access_log (
                user text,
                request timeuuid,
                request_update timeuuid,
                level text,
                endpoint text,
                method text,
                form_variables map<text, text>,
                get_variables map<text, text>,
                message text,
                PRIMARY KEY (user, request, request_update)
            ) WITH CLUSTERING ORDER BY (request DESC, request_update ASC)
        ''')

    class AccessLogger():

        def __init__(self, cassandra_cluster, user,
                     endpoint, method, form_variables, get_variables):
            self.cassandra_cluster = cassandra_cluster
            self.user = user
            self.request_timeuuid = generate_timeuuid()

            form_variables = _sanatize(form_variables)
            get_variables = _sanatize(get_variables)

            # store first record of endpoint access
            try:
                self.cassandra_cluster.session.execute(
                    self.cassandra_cluster.access_statement.bind((
                        user,
                        self.request_timeuuid,
                        self.request_timeuuid,
                        'init',
                        endpoint,
                        method,
                        form_variables,
                        get_variables,
                        None
                    ))
                )
            except:
                logger.exception('Database inaccessible!')

        def get_request_timeuuid(self):
            """
            return this request's timeuuid for external work
            :return:
            """
            return self.request_timeuuid

        def update(self, level, message):
            """
            Update record with Flask flash messages
            :param message:
            :return:
            """
            try:
                self.cassandra_cluster.session.execute(
                    self.cassandra_cluster.access_statement.bind((
                        self.user,
                        self.request_timeuuid,
                        generate_timeuuid(),
                        level,
                        None,
                        None,
                        None,
                        message
                    ))
                )
            except:
                logger.exeception('Database inaccessible!')

    def get_access_logger(self, request=None, user='Unauthenticated User'):
        """
        return access_logging object for Flask code
        :param request: Flask's request object
        :param user: Authenticated username
        :return:
        """
        return self.AccessLogger(self, user,
                                 str(request.url_rule), request.method,
                                 request.form, request.args)
