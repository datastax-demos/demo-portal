#!/usr/bin/env bash

# install prerequisites
sudo apt-get update
sudo apt-get install -y ruby-dev build-essential git-core tree python-pip python-dev libev4 libev-dev python-snappy

# check if vagrant.deb has been downloaded before. if not, download now. install.
if [ ! -f webapps/demo-portal/vagrant/vagrant-packages/vagrant_1.6.5_x86_64.deb ]; then
    mkdir -p webapps/demo-portal/vagrant/vagrant-packages

    wget --directory-prefix webapps/demo-portal/vagrant/vagrant-packages \
    https://dl.bintray.com/mitchellh/vagrant/vagrant_1.6.5_x86_64.deb
fi
sudo dpkg -i webapps/demo-portal/vagrant/vagrant-packages/vagrant_1.6.5_x86_64.deb

# setup the ~/ssh keys. ssh-keyscan github.com before cloning. chmod 600 ~/.ssh.
cp webapps/demo-portal/vagrant/keys/* .ssh
ssh-keyscan github.com >> .ssh/known_hosts
chmod 600 .ssh/*

# create logging directory
mkdir -p automaton_logs/joaquindatastaxcom

# setup automaton.conf
cp webapps/demo-portal/vagrant/keys/.automaton.conf ~

# needed to simulate a local dev environment
sudo chown -R ubuntu:ubuntu webapps

# setup vagrant to use the vagrant-aws and vagrant-awsinfo plugins
vagrant box add aws-dummy webapps/demo-portal/vagrant/vagrant-boxes/aws-dummy.box
vagrant plugin install vagrant-aws vagrant-awsinfo

# ensure we have a copy of the Vagrantfile
(
    cd ~/webapps/demo-portal/
    if [ ! -f vagrant/single-node-demo/Vagrantfile ]; then
        git checkout vagrant/single-node-demo/Vagrantfile
    fi
    if [ ! -f vagrant/web-gui/Vagrantfile ]; then
        git checkout vagrant/web-gui/Vagrantfile
    fi
)

(
    cd ~
    git clone automaton:riptano/automaton.git
    echo "export PYTHONPATH=~/automaton:${PYTHONPATH}" >> .profile
    echo "export PATH=~/automaton/bin:${PATH}" >> .profile

    cd automaton
    git pull
)

# WORKAROUND FOR: Python 2.7.8+
# install linux brew
sudo apt-get install build-essential curl git m4 ruby texinfo libbz2-dev libcurl4-openssl-dev libexpat-dev libncurses-dev zlib1g-dev
ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/linuxbrew/go/install)"

echo "export PATH=$HOME/.linuxbrew/bin:$PATH" >> .profile
echo "export MANPATH=$HOME/.linuxbrew/share/man:$MANPATH" >> .profile
echo "export INFOPATH=$HOME/.linuxbrew/share/info:$INFOPATH" >> .profile

source ~/.profile

brew install python

# END WORKAROUND

# install web-gui requirements
pip install -r ~/webapps/demo-portal/flask/requirements.txt

# set DEBUG mode to False when in ec2
if [ "$(whoami)" == "ubuntu" ]; then
    sed -i -e "s|DEBUG = True|DEBUG = False|g" ~/webapps/demo-portal/flask/web-gui.cfg
fi

# set the AWS credentials appropriately
source ~/webapps/demo-portal/set_credentials.sh

# kick off the web-gui
nohup python ~/webapps/demo-portal/flask/web-gui.py > out.log 2>&1 &

# ensure credentials are set on each launch
echo "source ~/webapps/demo-portal/set_credentials.sh" >> .profile

# setup ec2 cleaning cron job
sudo mkdir -p /mnt/logs
sudo chown ubuntu:ubuntu /mnt/logs/
sudo cp ~/webapps/demo-portal/cron/demo-portal.list /etc/cron.d/demoportal
