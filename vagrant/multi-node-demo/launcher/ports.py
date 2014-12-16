PORTS = {
    'dse': [
        # ## Public Facing Ports

        4040,  # Spark application web site port
        7080,  # Spark Master web site port
        7081,  # Spark Worker web site port
        8012,  # Hadoop Job Tracker client port
        8983,  # Solr port and Demo applications web site port
        50030,  # Hadoop Job Tracker web site port
        50060,  # Hadoop Task Tracker web site port

        # ## Inter-node Ports
        # ### Cassandra

        7000,  # Cassandra inter-node cluster communication port
        7001,  # Cassandra SSL inter-node cluster communication port
        7199,  # Cassandra JMX monitoring port
        9042,  # CQL native clients port
        9160,  # Cassandra client port (Thrift) port

        # ### DSE

        7077,  # Spark Master inter-node communication port
        8984,  # Solr inter-node communication port
        9290,  # Hadoop Job Tracker Thrift port
        10000,  # Hive/Shark server port

        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        8020,  # TODO: REMOVE: debugging weather sensors
    ],
    'opscenter': [
        # ## Public Facing Ports

        8888,  # OpsCenter web site port

        # ## Inter-node Ports
        # ### OpsCenter

        50031,  # OpsCenter HTTP proxy for Job Tracker port
        61620,  # OpsCenter monitoring port
        61621,  # OpsCenter agent port
    ],
    'connected-office': 3000,
    'weather-sensors': 3000,
}
