#!/usr/bin/env bash

# chown directories accordingly
sudo chown -R $(whoami):$(whoami) /portal

# add /sbin to PATH
echo "export PATH=/sbin:$PATH" >> ~/.profile

# install prerequisites
sudo apt-get update
sudo apt-get install -y ruby-dev build-essential git-core tree python-pip python-dev libev4 libev-dev python-snappy vim

# install Python 2.7.8+
(
    if [ ! -f /portal/python/bin/python ]; then
        sudo apt-get install -y libsqlite3-dev libbz2-dev libgdbm-dev libncurses5-dev tk-dev libreadline-dev libdb5.1-dev

        cd /tmp
        wget http://www.python.org/ftp/python/2.7.9/Python-2.7.9.tgz
        tar -zxvf Python-2.7.9.tgz
        cd Python-2.7.9
        mkdir /portal/python
        ./configure --prefix=/portal/python
        make
        make install

        echo "export PATH=/portal/python/bin:$PATH" >> ~/.profile
    fi
)

export PATH=/portal/python/bin:$PATH

(
    if [ ! -f /portal/virtualenv/bin/activate ]; then
        cd /tmp
        wget https://pypi.python.org/packages/source/v/virtualenv/virtualenv-12.0.5.tar.gz#md5=637abbbd04d270ee8c601ab29c4f7561
        tar -zxvf virtualenv-12.0.5.tar.gz
        cd virtualenv-12.0.5/
        /portal/python/bin/python setup.py install
        /portal/python/bin/virtualenv /portal/virtualenv --python /portal/python/bin/python2.7

        echo "source /portal/virtualenv/bin/activate" >> ~/.profile
    fi
)

source /portal/virtualenv/bin/activate

# check if vagrant.deb has been downloaded before. if not, download now. install.
if [ ! -f /portal/demo-portal/vagrant/vagrant-packages/vagrant_1.6.5_x86_64.deb ]; then
    mkdir -p /portal/demo-portal/vagrant/vagrant-packages

    wget --directory-prefix /portal/demo-portal/vagrant/vagrant-packages \
    https://dl.bintray.com/mitchellh/vagrant/vagrant_1.6.5_x86_64.deb
fi
sudo dpkg -i /portal/demo-portal/vagrant/vagrant-packages/vagrant_1.6.5_x86_64.deb

# setup the ~/ssh keys. ssh-keyscan github.com before cloning. chmod 600 ~/.ssh.
cp /portal/demo-portal/vagrant/keys/* .ssh
ssh-keyscan github.com >> .ssh/known_hosts
chmod 600 .ssh/*

# create logging directory
mkdir -p /portal/demo-portal/automaton_logs/joaquindatastaxcom

# setup automaton.conf
cp /portal/demo-portal/vagrant/keys/.automaton.conf ~

# setup vagrant to use the vagrant-aws and vagrant-awsinfo plugins
vagrant box add aws-dummy /portal/demo-portal/vagrant/vagrant-boxes/aws-dummy.box
vagrant plugin install vagrant-aws vagrant-awsinfo

(
    cd /portal/
    sudo chown -R $(whoami):$(whoami) /portal
    git clone automaton:riptano/automaton.git &&
    echo "export PYTHONPATH=/portal/automaton:${PYTHONPATH}" >> ~/.profile &&
    echo "export PATH=/portal/automaton/bin:${PATH}" >> ~/.profile

    cd /portal/automaton
    git pull
)

# install demo-portal requirements
pip install -r /portal/demo-portal/flask2.0/DemoPortalFlask/requirements.txt

# set DEBUG mode to False when in ec2
if [ -n "$PRODUCTION" ]; then
    sed -i -e "s|DEBUG.*|DEBUG = False|g" /portal/demo-portal/flask2.0/DemoPortalFlask/application.cfg
fi

# set the AWS credentials appropriately
source /portal/demo-portal/set_credentials.sh
echo "source /portal/demo-portal/set_credentials.sh" >> .profile

# kick off the demo-portal
# nohup python /portal/demo-portal/flask2.0/run > out.log 2>&1 &

# setup ec2 cleaning cron job
sudo mkdir -p /mnt/logs
sudo chown $(whoami):$(whoami) /mnt/logs/
sudo cp /portal/demo-portal/cron/demo-portal.list /etc/cron.d/demoportal
