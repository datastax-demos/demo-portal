# DataStax Demo Portal UI

This project serves the pre-sales team with full demo environments complete with
an application server and DSE instance(s).

## Setup

Install npm:

    brew install npm

Download required web components:

    npm install -g bower
    cd demo-portal/flask
    bower install
    
Install required Python packages:

    pip install -r requirements.txt

### OSX

You must install `md5sha1sum` using [brew](http://brew.sh/).

    brew install md5sha1sum

# Start Webserver locally

    cd demo-portal/flask
    source ../set_credentials.sh
    python web-gui.py

Then navigate to:

    http://localhost:5000.

# Run in AWS

## Setup

### Install Vagrant

https://www.vagrantup.com/downloads

### Install vagrant-aws plugin

    vagrant plugin install vagrant-aws
    vagrant box add aws-dummy https://github.com/mitchellh/vagrant-aws/raw/master/dummy.box

### Start the server

    cd demo-portal/vagrant/web-gui
    source ../../set_credentials.sh
    vagrant up --provider=aws --destroy-on-error

Using the `--provider=aws` option spins up a node in AWS where you can spin up
further nodes in AWS. Omitting the `--provider=aws` option will give you a local
VM for development purposes. You cannot, however, launch VMs within a VM.

**Note:** Using `--provider=aws` will only rsync data on `up`, `reload`, and
`provision`. More information can be found
[here](https://github.com/mitchellh/vagrant-aws#synced-folders).
    
### Find server IP address

    vagrant awsinfo -k public_ip

### Visit the web interface

    http://<ip>:5000

### Access server

    vagrant ssh
