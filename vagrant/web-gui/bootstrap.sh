#!/usr/bin/env bash

# install prerequisites
sudo apt-get update
sudo apt-get install -y ruby-dev build-essential git-core tree

# check if vagrant.deb has been downloaded before. if not, download now. install.
if [ ! -f webapps/demos-web-gui/vagrant/vagrant-packages/vagrant_1.6.5_x86_64.deb ]; then
    mkdir -p webapps/demos-web-gui/vagrant/vagrant-packages

    wget --directory-prefix webapps/demos-web-gui/vagrant/vagrant-packages \
    https://dl.bintray.com/mitchellh/vagrant/vagrant_1.6.5_x86_64.deb
fi
sudo dpkg -i webapps/demos-web-gui/vagrant/vagrant-packages/vagrant_1.6.5_x86_64.deb

# setup the ~/ssh keys. ssh-keyscan github.com before cloning. chmod 600 ~/.ssh.
cp webapps/demos-web-gui/vagrant/keys/* .ssh
ssh-keyscan github.com >> .ssh/known_hosts
cat .ssh/default-user.key.pub >> .ssh/authorized_keys
chmod 600 .ssh/*

# needed to simulate a local dev environment
mkdir webapps/datastax-dockerfiles
git clone git@datastax-dockerfiles:datastax-demos/datastax-dockerfiles.git webapps/datastax-dockerfiles

# setup vagrant to use the vagrant-aws plugin
vagrant box add aws-dummy webapps/demos-web-gui/vagrant/vagrant-boxes/aws-dummy.box
vagrant plugin install vagrant-aws

# ensure credentials are set on each launch
echo "source webapps/demos-web-gui/set_credentials.sh" >> .profile
