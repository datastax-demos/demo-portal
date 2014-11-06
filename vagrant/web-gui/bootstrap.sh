#!/usr/bin/env bash

# install prerequisites
sudo apt-get update
sudo apt-get install -y ruby-dev build-essential git-core tree python-pip python-dev

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
sudo chown -R ubuntu:ubuntu webapps

# setup vagrant to use the vagrant-aws and vagrant-awsinfo plugins
vagrant box add aws-dummy webapps/demos-web-gui/vagrant/vagrant-boxes/aws-dummy.box
vagrant plugin install vagrant-aws vagrant-awsinfo

# ensure we have a copy of the Vagrantfile
(
    cd ~/webapps/demos-web-gui/
    if [ ! -f vagrant/single-node-demo/Vagrantfile ]; then
        git checkout vagrant/single-node-demo/Vagrantfile
    fi
    if [ ! -f vagrant/web-gui/Vagrantfile ]; then
        git checkout vagrant/web-gui/Vagrantfile
    fi
)

# install web-gui requirements
sudo pip install -r ~/webapps/demos-web-gui/flask/requirements.txt

# set DEBUG mode to False when in ec2
if [ "$(whoami)" == "ubuntu" ]; then
    sed -i -e "s|DEBUG = True|DEBUG = False|g" ~/webapps/demos-web-gui/flask/web-gui.cfg
fi

# set the AWS credentials appropriately
source ~/webapps/demos-web-gui/set_credentials.sh

# kick off the web-gui
nohup python ~/webapps/demos-web-gui/flask/web-gui.py > out.log 2>&1 &

# ensure credentials are set on each launch
echo "source ~/webapps/demos-web-gui/set_credentials.sh" >> .profile

# setup ec2 cleaning cron job
sudo cp ~/webapps/demos-web-gui/cron/demos-web-gui.list /etc/cron.d/
