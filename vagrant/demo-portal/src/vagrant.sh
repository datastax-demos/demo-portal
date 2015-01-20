#!/bin/sh

# check if vagrant.deb has been downloaded before. if not, download now.
if [ ! -f /cache/vagrant_1.6.5_x86_64.deb ]; then
    wget --directory-prefix /cache \
    https://dl.bintray.com/mitchellh/vagrant/vagrant_1.6.5_x86_64.deb
fi
sudo dpkg -i /cache/vagrant_1.6.5_x86_64.deb

# setup vagrant to use the vagrant-aws and vagrant-awsinfo plugins
vagrant box add aws-dummy /portal/demo-portal/vagrant/vagrant-boxes/aws-dummy.box
vagrant plugin install vagrant-aws vagrant-awsinfo
