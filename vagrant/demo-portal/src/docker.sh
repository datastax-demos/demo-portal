#!/bin/sh

cp /portal/demo-portal/vagrant/keys/.dockercfg .
chmod 600 .dockercfg

sudo cp /portal/demo-portal/vagrant/keys/.dockercfg /root
sudo chmod 600 /root .dockercfg

mkdir -p /cache/docker

CACHE=/cache/docker
FILENAME=datastaxdemos_datastax-enterprise.container
if [ ! -f ${CACHE}/${FILENAME} ]; then
    sudo docker pull datastaxdemos/datastax-enterprise
    sudo docker save --output ${CACHE}/${FILENAME} datastaxdemos/datastax-enterprise
fi
sudo docker load --input ${CACHE}/${FILENAME}
