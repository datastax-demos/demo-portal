#!/usr/bin/env bash

# install prerequisites
sudo apt-get update
sudo apt-get install -y build-essential tree git-core

# setup the ~/ssh keys. ssh-keyscan github.com before cloning. chmod 600 ~/.ssh.
cp webapps/demos-web-gui/vagrant/keys/* .ssh
ssh-keyscan github.com >> .ssh/known_hosts
chmod 600 .ssh/*

# ensure credentials are set on each launch
echo "source webapps/demos-web-gui/set_credentials.sh" >> .profile

# preconfigure the ubuntu/datastax image, for dev purposes
source webapps/demos-web-gui/set_credentials.sh
