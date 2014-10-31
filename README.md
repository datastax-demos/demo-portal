# Demo Web GUI

This project serves the pre-sales team with full demo environments complete with
an application server and DSE instance(s).

## Setup

Install Vagrant: https://www.vagrantup.com/downloads

Install vagrant-aws plugin:

    vagrant plugin install vagrant-aws
    vagrant box add aws-dummy https://github.com/mitchellh/vagrant-aws/raw/master/dummy.box

Using the `--provider=aws` option spins up a node in AWS where you can spin up
further nodes in AWS. Omitting the `--provider=aws` option will give you a local
VM for development purposes. You cannot, however, launch VMs within a VM.

**Note:** Using `--provider=aws` will only rsync data on `up`, `reload`, and
`provision`. More information can be found
[here](https://github.com/mitchellh/vagrant-aws#synced-folders).

## Run web-gui Vagrantfile

    cd vagrant/web-gui
    vagrant up [--provider=aws]

## Run single-node-demo Vagrantfile

    cd vagrant/single-node-demo
    vagrant up [--provider=aws]

    # TODO: Automatically swap AZs.
