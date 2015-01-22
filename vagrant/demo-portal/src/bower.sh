#!/bin/sh

# install nodejs
wget -c http://nodejs.org/dist/v0.10.35/node-v0.10.35-linux-x64.tar.gz -P /cache
tar -zxvf /cache/node-v0.10.35-linux-x64.tar.gz --directory /portal
mv /portal/node* /portal/node

# set PATH to include nodejs
export PATH=/portal/node/bin:${PATH}
echo "export PATH=/portal/node/bin:${PATH}" >> .profile

# install npmbox
cp /portal/demo-portal/vagrant/npm/npmbox.npmbox /tmp
tar -xvf /tmp/npmbox.npmbox --directory /tmp
npm install --global --cache /tmp/.npmbox-cache --optional --cache-min 999999 --fetch-retries 0 --fetch-retry-factor 0 --fetch-retry-mintimeout 1 --fetch-retry-maxtimeout 2 npmbox

# install bower
(
    cd /portal/demo-portal/vagrant/npm/
    npmunbox -g bower.npmbox
)
