#!/usr/bin/env bash

# install prerequisites
sudo apt-get update
sudo apt-get install -y build-essential tree git-core python-pip
sudo pip install boto

# setup the ~/ssh keys. ssh-keyscan github.com before cloning. chmod 600 ~/.ssh.
cp webapps/demos-web-gui/vagrant/keys/* .ssh
cp webapps/demos-web-gui/vagrant/keys/.dockercfg .
sudo cp webapps/demos-web-gui/vagrant/keys/.dockercfg /root
cat .ssh/default-user.key.pub >> .ssh/authorized_keys
ssh-keyscan github.com >> .ssh/known_hosts
chmod 600 .ssh/*
chmod 600 .dockercfg
sudo chmod 600 /root .dockercfg

# ensure credentials are set on each launch
echo "source webapps/demos-web-gui/set_credentials.sh" >> .profile

# preconfigure the ubuntu/datastax image, for dev purposes
source webapps/demos-web-gui/set_credentials.sh
