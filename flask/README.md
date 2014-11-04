# Demo Web GUI

This project serves the pre-sales team with full demo environments complete with
an application server and DSE instance(s).

## Setup

Download required web components:

    npm install -g bower
    bower install
    
Install required Python packages:

    pip install -r requirements.txt

Install vagrant-aws plugin:

    vagrant plugin install vagrant-aws
    vagrant box add aws-dummy https://github.com/mitchellh/vagrant-aws/raw/master/dummy.box

## Start Webserver

    python web-gui.py

Then navigate to: http://localhost:500x.

# Run in AWS

Start the server using:

    vagrant up --provider=aws

Hop onto the server using:

    vagrant ssh
    
Find server IP address using:

    vagrant awsinfo -k public_ip

Visit the web interface by visiting:

    http://<ip>:5000
