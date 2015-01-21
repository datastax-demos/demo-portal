This script should be used to stand up a new DataStax Demo Portal
if the current one were to fall.

## SSH Access

SSH access on each of these machines is slightly different than typical vagrant
setups since all other machines require AWS credentials. Because of this, you'll
need to specify the vagrant machine to ssh into. Example:

    vagrant ssh dev

# Dev

    vagrant up dev

This machine spins up a local VirtualBox VM with the exact same packages that
are installed on all other machines, except for a few key differences:

* Vagrant synced folders are used to allow file editing on the host machine to
instantly be available on the guest machine.
* Caching is used whenever possible and stored in `vagrant/cache` on the host
machine and `/cache` on the guest machine to shave build time from 17 minutes
down to 6 minutes.
* The VM will always start up with the address: http://192.168.133.7:5000
* The website is not automatically started, instead you must run:

```
vagrant ssh dev
python /portal/demo-portal/flask2.0/run
```

# Production A/B

    vagrant up production-A
    vagrant up production-B

# Staging

    vagrant up staging

# Build

    vagrant up build
