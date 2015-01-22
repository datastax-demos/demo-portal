import datetime

from uuid import UUID as pyUUID, getnode

from cassandra.cluster import Cluster
from cassandra.query import ordered_dict_factory

from DemoPortalFlask.logic.logger import logger


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
    output = input_dict.copy()
    if 'current-password' in output:
        output['current-password'] = '******'
    if 'new-password' in output:
        output['new-password'] = '******'
    if 'confirm-password' in output:
        output['confirm-password'] = '******'
    return output


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
                user text,
                form_variables map<text, text>,
                time timestamp,
                PRIMARY KEY ((date), request)
            ) WITH CLUSTERING ORDER BY (request DESC)
        ''')

        self.session.execute('''
            CREATE TABLE IF NOT EXISTS demo_portal.demo_launches (
                demo text,
                request timeuuid,
                user text,
                form_variables map<text, text>,
                time timestamp,
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

        self.session.execute('''
            CREATE TABLE IF NOT EXISTS demo_portal.users (
                user text,
                admin boolean,
                password_hash text,
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
                (date, request, demo, user, form_variables, time)
            VALUES
                (?, ?, ?, ?, ?, ?)
        ''')

        self.insert_demo_launch_statement = self.session.prepare('''
            INSERT INTO demo_portal.demo_launches
                (demo, request, user, form_variables, time)
            VALUES
                (?, ?, ?, ?, ?)
        ''')

        self.insert_last_seen_statement = self.session.prepare('''
            INSERT INTO demo_portal.last_seen
                (user, date)
            VALUES
                (?, ?)
        ''')

        self.insert_password_statement = self.session.prepare('''
            INSERT INTO demo_portal.users
                (user, password_hash)
            VALUES
                (?, ?)
        ''')

        self.query_access_log_statement = self.session.prepare('''
            SELECT * FROM demo_portal.access_log
            WHERE date=?
        ''')

        self.query_user_access_log_statement = self.session.prepare('''
            SELECT * FROM demo_portal.user_access_log
            WHERE user=?
        ''')

        self.query_last_seen_statement = self.session.prepare('''
            SELECT * FROM demo_portal.last_seen
        ''')

        self.query_launches_statement = self.session.prepare('''
            SELECT * FROM demo_portal.launches
        ''')

        self.query_demo_launches_statement = self.session.prepare('''
            SELECT * FROM demo_portal.demo_launches
        ''')

        self.query_user_statement = self.session.prepare('''
            SELECT * FROM demo_portal.users
            WHERE user = ?
        ''')

    def set_password(self, user, password):
        """
        Set user password
        :param user: email
        :param password: hashed password
        :return:
        """
        self.session.execute(
            self.insert_password_statement.bind((user, password)))

    def get_user(self, user):
        """
        Return the saved user record
        :param user: email
        :return:
        """
        return self.session.execute(self.query_user_statement.bind((user,)))

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
                        self.user,
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
                        self.user,
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
                        self.user,
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

        def get_access_log(self, date):
            """
            return an admin's view of history
            :param date: date partition key
            :return:
            """
            all_rows = []
            for row in self.cassandra_cluster.session.execute(
                    self.cassandra_cluster.query_access_log_statement.bind((
                            date,
                    ))):
                all_rows.append(row)

            return all_rows

        def get_user_access_log(self, user):
            """
            return a user's history
            :param user: user name
            :return:
            """
            all_rows = []
            for row in self.cassandra_cluster.session.execute(
                    self.cassandra_cluster.query_user_access_log_statement.bind(
                            (
                                    user,
                            ))):
                all_rows.append(row)

            return all_rows

        def get_last_seen_log(self):
            """
            return the "last seen" log
            :return:
            """
            all_rows = []
            for row in self.cassandra_cluster.session.execute(
                    self.cassandra_cluster.query_last_seen_statement):
                all_rows.append(row)

            return all_rows

        def get_launches(self):
            """
            return the "last seen" log
            :return:
            """
            all_rows = []
            for row in self.cassandra_cluster.session.execute(
                    self.cassandra_cluster.query_launches_statement):
                all_rows.append(row)

            return all_rows

        def get_demo_launches(self):
            """
            return the "last seen" log
            :return:
            """
            all_rows = []
            for row in self.cassandra_cluster.session.execute(
                    self.cassandra_cluster.query_demo_launches_statement):
                all_rows.append(row)

            return all_rows

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
                        self.user,
                        self.form_variables,
                        datetime.datetime.now()
                    ))
                )
                self.cassandra_cluster.session.execute(
                    self.cassandra_cluster.insert_demo_launch_statement.bind((
                        demo,
                        self.request_timeuuid,
                        self.user,
                        self.form_variables,
                        datetime.datetime.now()
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
