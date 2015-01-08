# DataStax Demo Portal Launching Infrastructure

This directory is used for launching Dockerized containers through the
DataStax Demo Portal.

## new-cluster

`new-cluster` is called from our `/flask` server and copies this directory into 
`$DEMO_WEB_GUI_ROOT/launched-clusters/${TIMESTAMP}-${CLEAN_EMAIL}-${CLEAN_DEMO}`
. It then starts the `launch_demo` script.

This copying is done since a `.vagrant` directory is added to the current
working directory and multi-tenancy would not be available if all tenants used
the same directory.

These directories allow us to investigate possible issues as well.

## launch_demo

`launch_demo` starts the Vagrant nodes using the AWS provider.
Grabs the IP addresses of the provisioned nodes.
Provisions the nodes using the Docker provisioner.
All work is done in parallel to help start times.

## launcher/

`launcher/` contains the logic for the `launch_demo` script.

## Vagrantfile and bootstrap.sh

These are the files used by the Vagrant command.
