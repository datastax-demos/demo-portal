This script should be used to stand up a new DataStax Demo Portal
if the current one were to fall.

### SSH Access

SSH access on each of these machines is slightly different than typical vagrant
setups since all other machines require AWS credentials. Because of this, you'll
need to specify the vagrant machine to ssh into. Example:

    vagrant ssh dev
    vagrant ssh dev-stale
    vagrant ssh production-A
    vagrant ssh production-B
    vagrant ssh staging
    vagrant ssh build
    vagrant ssh dse

## provision(production, stale)

The provision function in Vagrantfile ensures that each defined machine will
share the same processes. The differences are as follows:

### Production

#### true

* `$PRODUCTION=1` is set on the provisioned machines
* `$DEMO_PROD_CASS`, which defaults to 54.164.166.255, will be used for the
DataStax Enterprise IP.

**Note:** When provisioning with `production=true`, you must grab
`vagrant awsinfo -m <machine_name> -k public_ip` as the node launches and add
a `New Rule` to the AWS security group [here]
(https://us-3.rightscale.com/acct/73292/network_manager#networks/8JJ1403KL5DHJ/security_groups/F1N2PPFA0IPNE):

* Direction: Inbound
* Protocol: All Protocols - IPs
* IP Range: `vagrant awsinfo -m <machine_name> -k public_ip` output

Permissions to the `IT - Sysadmin` Rightscale account are required.

#### false

* A local DataStax Enterprise debian package install will occur.
* 127.0.0.1 will be used as the IP address for the DataStax Enterprise machine.

### Stale

#### true

All syncs will be one-way syncs to the new machine.

* `../keys/demo-portal.key` ==> `~/.ssh/demo-portal.key`.
* `../keys/config` ==> `~/.ssh/config`.
* The `demo-portal` repository will be cloned directly from Github.
* `../../set_credentials.sh` ==>
`/portal/demo-portal/set_credentials.sh`.
* `../../flask2.0/DemoPortalFlask/application.cfg` ==>  
`/portal/demo-portal/flask2.0/DemoPortalFlask/application.cfg`.
* `../keys` ==> `/portal/demo-portal/vagrant/`.

#### false

All syncs will be two-way syncs between the host machine and guest machine.

* `../..` <==> `/portal/demo-portal`.
* `../cache` <==> `/cache`.

## Dev

    vagrant up dev

    provision(production: false, stale: false)

This command should be run when developing on the demo-portal. Access to a local
copy of the site will start automatically at http://192.168.133.7:5000.

## Dev Stale

    vagrant up dev-stale

    provision(production: false, stale: true)

This command should be run when ensuring cloud builds work as intended, without
hitting the production DataStax Enterprise cluster. Access to a local
copy of the site will start automatically at http://192.168.133.8:5000.

## Production A/B

    vagrant up production-A
    vagrant up production-B

    provision(production: true, stale: true)
    provision(production: true, stale: true)

This command should be used to launch a new release of the Demo Portal. Two
commands exist to allow for seamless DNS switching to occur as the machines
are upgraded through IP rotation.

When performing an IP rotation, ensure helpdesk@datastax.com updates the
demos.datastax.com DNS.

## Staging

    vagrant up staging

    provision(production: true, stale: true)

This command should be used for beta-testing the Demo Portal. Access to this
site will be available at staging.demos.datastax.com, but can be taken offline
routinely and may experience a high number of bugs due to high code churn.

## Build

    vagrant up build

    provision(production: true, stale: true)

This command should be used to beta-test the build process at the same level as
the Production A/B machine without stressing too much on killing the wrong
machine.

## DSE

    vagrant up dse

This machine is different from the rest and should be included with the build
machine in the following fashion:

    vagrant up dse
    DEMO_PROD_CASS=$(vagrant awsinfo -m dse -k public_ip)
    vagrant up build
    unset DEMO_PROD_CASS

Then visit port 5000 of the following machine:

    vagrant awsinfo -m build -k public_ip

This should be the ideal way to test the build process since it starts
everything from scratch each time.

If this machine ever becomes relied on, make sure to update the default value
of `$DEMO_PROD_CASS` in Vagrantfile to be the public IP address for the new
DataStax Enterprise node.
