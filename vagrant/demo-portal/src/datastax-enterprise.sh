#!/bin/sh

DATASTAX_USER=demos_datastax.com
DATASTAX_PASS=6i8Cjv3lmdKqf01

# cache and install dse
CACHE=/cache/apt/datastax-enterprise
if [ ! -d ${CACHE} ]; then
    mkdir -p ${CACHE}

    # setup repository access
    echo "deb http://${DATASTAX_USER}:${DATASTAX_PASS}@debian.datastax.com/enterprise stable main" | \
        sudo tee -a /etc/apt/sources.list.d/datastax.sources.list
    curl -L https://debian.datastax.com/debian/repo_key | sudo apt-key add -
    sudo apt-get update

    PACKAGES='dse-full'
    apt-get --print-uris --yes install $PACKAGES | grep ^\' | cut -d\' -f2 > ${CACHE}.list
    wget -c -i ${CACHE}.list -P ${CACHE}
fi
sudo dpkg -i ${CACHE}/*

sudo sed -i -e "s|^#MAX_HEAP_SIZE=.*|MAX_HEAP_SIZE=\"750M\"|g" /etc/dse/cassandra/cassandra-env.sh
sudo sed -i -e "s|^#HEAP_NEWSIZE=.*|HEAP_NEWSIZE=\"200M\"|g" /etc/dse/cassandra/cassandra-env.sh

# start dse
sudo service dse start

# wait for Cassandra's native transport to start
while :
do
    echo "SELECT bootstrapped FROM system.local;" | cqlsh 127.0.0.1 && break
    sleep 1
done
