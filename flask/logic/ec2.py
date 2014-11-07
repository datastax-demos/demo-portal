#!/usr/local/bin python

import boto.ec2
import os
import pprint

from collections import defaultdict


def owned_instances(email='joaquin@datastax.com', region='us-east-1',
                    admin=False):
    conn = boto.ec2.connect_to_region(region,
                                      aws_access_key_id=os.environ[
                                          'AWS_ACCESS_KEY'],
                                      aws_secret_access_key=os.environ[
                                          'AWS_SECRET_KEY'])

    return_value = defaultdict(dict)
    reservations = conn.get_all_reservations()
    for reservation in reservations:
        instances = reservation.instances
        for instance in instances:
            if 'provisioner' in instance.tags \
                    and instance.tags['provisioner'] == \
                            'demos-web-gui-launcher' \
                    and instance.state != 'terminated':
                if admin or instance.tags['email'] == email:
                    return_value[reservation.id][instance.ami_launch_index] = {
                        'state': instance.state,
                        'reservation_size': len(reservation.instances),
                        'instance_type': instance.instance_type,
                        'ip_address': instance.ip_address,
                        'launch_time': instance.launch_time,
                        'tags': instance.tags,
                    }

                    if admin:
                        return_value[reservation.id][instance.ami_launch_index][
                            'email'] = instance.tags['email']

    return dict(return_value)


def kill_reservation(reservationid, region='us-east-1'):
    conn = boto.ec2.connect_to_region(region,
                                      aws_access_key_id=os.environ[
                                          'AWS_ACCESS_KEY'],
                                      aws_secret_access_key=os.environ[
                                          'AWS_SECRET_KEY'])

    reservation = \
        conn.get_all_instances(filters={'reservation-id': reservationid})[0]
    instances = [i.id for i in reservation.instances]

    conn.terminate_instances(instance_ids=instances)
    return True


def main():
    owned_instances_data = owned_instances()
    pprint.pprint(owned_instances_data)


if __name__ == '__main__':
    main()
