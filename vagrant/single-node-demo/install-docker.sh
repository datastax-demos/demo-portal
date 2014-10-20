#!/usr/bin/env bash

# check that HTTPS transport is available to APT
if [ ! -e /usr/lib/apt/methods/https ]; then
	apt-get update
	apt-get install -y apt-transport-https
fi

# add the repository to your APT sources
echo deb https://get.docker.com/ubuntu docker main > /etc/apt/sources.list.d/docker.list

# then import the repository key
apt-key add webapps/demos-web-gui/vagrant/keys/Docker.repo.key

# install docker
apt-get update
apt-get install -y lxc-docker
