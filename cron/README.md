This directory houses our cloud cleanup scripts.

This is setup using `/vagrant/web-gui` on the
DataStax Demo Portal.

## demo-portal.list

`demo-portal.list` is copied to `/etc/cron.d/demoportal`.

This cronjob is currently run every minute. Change 1
to 5 make it run every 5, etc.

## kicker

This script is used to ensure the cronjob never
has to be restarted with the credentials appropriately set
by setting the credentials and kicking off `cleanup` while
piping the output to `/mnt/logs/cron.log`.

## cleanup

Does the actual cloud cleanup.

## create_logger.py

Is a helper script for logging `cleanup`.

