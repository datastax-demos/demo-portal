import boto.ec2
import os


def tag(instance_id, key, value, region='us-east-1'):
    conn = boto.ec2.connect_to_region(region,
                                      aws_access_key_id=os.environ[
                                          'AWS_ACCESS_KEY'],
                                      aws_secret_access_key=os.environ[
                                          'AWS_SECRET_KEY'])

    reservations = conn.get_all_instances(instance_ids=[instance_id])
    instance = reservations[0].instances[0]
    instance.add_tag(key, value)
