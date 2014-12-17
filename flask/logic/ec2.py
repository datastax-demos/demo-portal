#!/usr/local/bin python

import boto.ec2
import os
import pprint

from collections import defaultdict


def owned_instances(email='joaquin@datastax.com', conn=False,
                    region='us-east-1', admin=False):
    if not conn:
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
                            'demo-portal-launcher' \
                    and instance.state != 'terminated' \
                    and instance.state != 'shutting-down':
                if admin or instance.tags['email'] == email:
                    return_value[reservation.id][instance.ami_launch_index] = {
                        'instance_id': instance.id,
                        'reservation_id': reservation.id,
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


def tag(instance_ids, key, value, conn=False, region='us-east-1'):
    if not conn:
        conn = boto.ec2.connect_to_region(region,
                                          aws_access_key_id=os.environ[
                                              'AWS_ACCESS_KEY'],
                                          aws_secret_access_key=os.environ[
                                              'AWS_SECRET_KEY'])

    instance_ids = instance_ids.split(',')
    reservations = conn.get_all_instances(instance_ids=instance_ids)
    instance = reservations[0].instances[0]
    instance.add_tag(key, value)


def find_reservation_id_by_tag(key, value, conn=False, region='us-east-1'):
    if not conn:
        conn = boto.ec2.connect_to_region(region,
                                          aws_access_key_id=os.environ[
                                              'AWS_ACCESS_KEY'],
                                          aws_secret_access_key=os.environ[
                                              'AWS_SECRET_KEY'])

    reservation = \
        conn.get_all_instances(filters={'tag:%s' % key: value})[0]

    return reservation.id


def get_reservation_instances(reservation_id, conn=False, region='us-east-1'):
    if not conn:
        conn = boto.ec2.connect_to_region(region,
                                          aws_access_key_id=os.environ[
                                              'AWS_ACCESS_KEY'],
                                          aws_secret_access_key=os.environ[
                                              'AWS_SECRET_KEY'])

    reservation = \
        conn.get_all_instances(filters={'reservation-id': reservation_id})[0]
    instances = [i.id for i in reservation.instances]

    return instances


def tag_reservation(reservation_id, key, value, conn=False, region='us-east-1'):
    if not conn:
        conn = boto.ec2.connect_to_region(region,
                                          aws_access_key_id=os.environ[
                                              'AWS_ACCESS_KEY'],
                                          aws_secret_access_key=os.environ[
                                              'AWS_SECRET_KEY'])

    instances = get_reservation_instances(reservation_id, conn=conn, region=region)

    for instance in instances:
        tag(instance, key, value, conn=conn, region=region)


def kill_reservation(reservation_id, conn=False, region='us-east-1'):
    if not conn:
        conn = boto.ec2.connect_to_region(region,
                                          aws_access_key_id=os.environ[
                                              'AWS_ACCESS_KEY'],
                                          aws_secret_access_key=os.environ[
                                              'AWS_SECRET_KEY'])

    tag_reservation(reservation_id, 'status', 'Terminating.',
                    conn=conn, region=region)

    instances = get_reservation_instances(reservation_id, conn=conn, region=region)
    conn.terminate_instances(instance_ids=instances)
    return True


def main():
    owned_instances_data = owned_instances()
    pprint.pprint(owned_instances_data)


if __name__ == '__main__':
    main()
