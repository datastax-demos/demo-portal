#!/usr/bin/env bash

# install prerequisites
sudo apt-get update
sudo apt-get install -y build-essential tree git-core python-pip
sudo pip install boto

# setup the ~/ssh keys. ssh-keyscan github.com before cloning. chmod 600 ~/.ssh.
cp webapps/demo-portal/vagrant/keys/* .ssh
cp webapps/demo-portal/vagrant/keys/.dockercfg .
sudo cp webapps/demo-portal/vagrant/keys/.dockercfg /root
cat .ssh/default-user.key.pub >> .ssh/authorized_keys
ssh-keyscan github.com >> .ssh/known_hosts
chmod 600 .ssh/*
chmod 600 .dockercfg
sudo chmod 600 /root .dockercfg

# ensure credentials are set on each launch
echo "source webapps/demo-portal/set_credentials.sh" >> .profile

# preconfigure the ubuntu/datastax image, for dev purposes
source webapps/demo-portal/set_credentials.sh
