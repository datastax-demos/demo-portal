import datetime

from uuid import UUID as pyUUID, getnode

from cassandra.cluster import Cluster
from cassandra.query import ordered_dict_factory

from logger import logger


def generate_timeuuid():
    """
    code modified from: http://goo.gl/czeA4P
    """
    dt = datetime.datetime.now()

    epoch = datetime.datetime(1970, 1, 1, tzinfo=dt.tzinfo)
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
            self.session.row_factory = ordered_dict_factory

            # ensure schema is created
            self.initialize_schema()

            # prepare access insert and query statements
            self.prepare_statements()
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
                date timestamp,
                request timeuuid,
                request_update timeuuid,
                user text,
                level text,
                endpoint text,
                method text,
                form_variables map<text, text>,
                get_variables map<text, text>,
                message text,
                PRIMARY KEY ((date), request, request_update)
            ) WITH CLUSTERING ORDER BY (request DESC, request_update ASC)
        ''')

        self.session.execute('''
            CREATE TABLE IF NOT EXISTS demo_portal.user_access_log (
                user text,
                request timeuuid,
                request_update timeuuid,
                level text,
                endpoint text,
                method text,
                form_variables map<text, text>,
                get_variables map<text, text>,
                message text,
                PRIMARY KEY ((user), request, request_update)
            ) WITH CLUSTERING ORDER BY (request DESC, request_update ASC)
        ''')

        self.session.execute('''
            CREATE TABLE IF NOT EXISTS demo_portal.launches (
                date timestamp,
                request timeuuid,
                demo text,
                form_variables map<text, text>,
                PRIMARY KEY ((date), request)
            ) WITH CLUSTERING ORDER BY (request DESC)
        ''')

        self.session.execute('''
            CREATE TABLE IF NOT EXISTS demo_portal.demo_launches (
                demo text,
                request timeuuid,
                user text,
                form_variables map<text, text>,
                PRIMARY KEY ((demo), request)
            ) WITH CLUSTERING ORDER BY (request DESC)
        ''')

        self.session.execute('''
            CREATE TABLE IF NOT EXISTS demo_portal.last_seen (
                user text,
                date timestamp,
                PRIMARY KEY ((user))
            )
        ''')

    def prepare_statements(self):
        self.insert_access_statement = self.session.prepare('''
            INSERT INTO demo_portal.access_log
                (date, request, request_update,
                user, level, endpoint, method, form_variables,
                get_variables,
                message)
            VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''')

        self.insert_user_access_statement = self.session.prepare('''
            INSERT INTO demo_portal.user_access_log
                (user, request, request_update,
                level, endpoint, method, form_variables, get_variables,
                message)
            VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''')

        self.insert_launch_statement = self.session.prepare('''
            INSERT INTO demo_portal.launches
                (date, request, demo, form_variables)
            VALUES
                (?, ?, ?, ?)
        ''')

        self.insert_demo_launch_statement = self.session.prepare('''
            INSERT INTO demo_portal.demo_launches
                (demo, request, user, form_variables)
            VALUES
                (?, ?, ?, ?)
        ''')

        self.insert_last_seen_statement = self.session.prepare('''
            INSERT INTO demo_portal.last_seen
                (user, date)
            VALUES
                (?, ?)
        ''')

        self.query_user_history_statement = self.session.prepare('''
            SELECT * FROM demo_portal.user_access_log
            WHERE user=?
        ''')

    class AccessLogger():
        def __init__(self, cassandra_cluster, user,
                     endpoint, method, form_variables, get_variables,
                     init_log):
            self.cassandra_cluster = cassandra_cluster
            self.user = user

            # https://datastax-oss.atlassian.net/browse/PYTHON-212
            self.today = datetime.datetime.combine(datetime.date.today(),
                                                   datetime.datetime.min.time())
            self.request_timeuuid = generate_timeuuid()

            self.form_variables = _sanatize(form_variables)
            self.get_variables = _sanatize(get_variables)

            if not init_log:
                return

            # store first record of endpoint access
            try:
                self.cassandra_cluster.session.execute(
                    self.cassandra_cluster.insert_access_statement.bind((
                        self.today,
                        self.request_timeuuid,
                        self.request_timeuuid,
                        user,
                        'init',
                        endpoint,
                        method,
                        self.form_variables,
                        self.get_variables,
                        None
                    ))
                )
                self.cassandra_cluster.session.execute(
                    self.cassandra_cluster.insert_user_access_statement.bind((
                        user,
                        self.request_timeuuid,
                        self.request_timeuuid,
                        'init',
                        endpoint,
                        method,
                        self.form_variables,
                        self.get_variables,
                        None
                    ))
                )
                self.cassandra_cluster.session.execute(
                    self.cassandra_cluster.insert_last_seen_statement.bind((
                        user,
                        datetime.datetime.now()
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

        def get_history(self, user):
            """
            return a user's history
            :param user: user name
            :return:
            """
            return self.cassandra_cluster.session.execute(
                self.cassandra_cluster.query_user_history_statement.bind((
                    user,
                ))
            )

        def update(self, level, message):
            """
            Update record with Flask flash messages
            :param message: flash message
            :return:
            """
            try:
                self.cassandra_cluster.session.execute(
                    self.cassandra_cluster.insert_access_statement.bind((
                        self.today,
                        self.request_timeuuid,
                        generate_timeuuid(),
                        self.user,
                        level,
                        None,
                        None,
                        None,
                        message
                    ))
                )
                self.cassandra_cluster.session.execute(
                    self.cassandra_cluster.insert_user_access_statement.bind((
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
                logger.exception('Database inaccessible!')

        def launch(self, demo):
            """
            Update records for demo launches
            :param demo: name of the launched demo
            :return:
            """
            try:
                self.cassandra_cluster.session.execute(
                    self.cassandra_cluster.insert_launch_statement.bind((
                        self.today,
                        self.request_timeuuid,
                        demo,
                        self.form_variables
                    ))
                )
                self.cassandra_cluster.session.execute(
                    self.cassandra_cluster.insert_demo_launch_statement.bind((
                        demo,
                        self.request_timeuuid,
                        self.user,
                        self.form_variables
                    ))
                )
            except:
                logger.exception('Database inaccessible!')

    def get_access_logger(self, request=None, user='Unauthenticated User',
                          init_log=True):
        """
        return access_logging object for Flask code
        :param request: Flask's request object
        :param user: Authenticated username
        :return:
        """
        return self.AccessLogger(self, user,
                                 str(request.url_rule), request.method,
                                 request.form, request.args,
                                 init_log)
