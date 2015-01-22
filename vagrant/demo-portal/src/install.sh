#!/bin/sh

# get code!

# setup the ~/ssh keys. chmod 600 ~/.ssh.
cp /portal/demo-portal/vagrant/keys/* .ssh
chmod 600 .ssh/*

# create logging directory
mkdir -p /portal/demo-portal/automaton_logs/joaquindatastaxcom

# setup automaton.conf
cp /portal/demo-portal/vagrant/keys/.automaton.conf .

# install demo-portal Python requirements
pip install --download-cache /cache/pip -r /portal/demo-portal/flask2.0/DemoPortalFlask/requirements.txt
pip install --download-cache /cache/pip cqlsh

# install demo-portal bower requirements
(
    cd /portal/demo-portal/flask2.0/DemoPortalFlask
    bower --config.analytics=false install
)

# set DEBUG mode to False when in ec2
if [ -n "$PRODUCTION" ]; then
    sed -i -e "s|DEBUG.*|DEBUG = False|g" /portal/demo-portal/flask2.0/DemoPortalFlask/application.cfg
    sed -i -e "s|DSE_CLUSTER.*|DSE_CLUSTER = '127.0.0.1'|g" /portal/demo-portal/flask2.0/DemoPortalFlask/application.cfg
fi

# set the AWS credentials appropriately
echo "source /portal/demo-portal/set_credentials.sh" >> .profile

# setup ec2 cleaning cron job
sudo mkdir -p /mnt/logs
sudo chown $(whoami):$(whoami) /mnt/logs/
sudo cp /portal/demo-portal/cron/demo-portal.list /etc/cron.d/demoportal

# install automaton
CACHE=/cache/automaton
if [ ! -d ${CACHE} ]; then
    (
        cd /cache
        git clone automaton:riptano/automaton.git
    )
fi
cp -r ${CACHE} /portal
echo "export PYTHONPATH=/portal/automaton:${PYTHONPATH}" >> .profile
echo "export PATH=/portal/automaton/bin:${PATH}" >> .profile

(
    cd /portal/automaton
    git pull
)
