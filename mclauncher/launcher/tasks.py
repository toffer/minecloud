import boto
import boto.ec2
import datetime
import os
import time

from celery import task
from django.template.loader import render_to_string
from django.utils.timezone import utc
from django_sse.redisqueue import send_event

from .models import Instance

@task
def launch(instance_id):
    # Retrive instance obj from DB.
    instance = Instance.objects.get(pk=instance_id)

    # Set variables to launch EC2 instance
    ec2_ami = os.getenv('MCL_EC2_AMI')
    ec2_region = os.getenv('MCL_EC2_REGION', 'us-west-2')
    ec2_keypair = os.getenv('MCL_EC2_KEYPAIR','MinecraftEC2')
    ec2_instancetype = os.getenv('MCL_EC2_INSTANCE_TYPE', 'm1.small')
    ec2_secgroups = [os.getenv('MCL_EC2_SECURITY_GROUP', 'minecraft')]

    # ec2_env_vars populate the userdata.txt file. Cloud-init will append
    # them to /etc/environment on the launched EC2 instance during bootup.
    ec2_env_vars = {'AWS_ACCESS_KEY_ID': os.getenv('AWS_ACCESS_KEY_ID'),
                    'AWS_SECRET_ACCESS_KEY': os.getenv('AWS_SECRET_ACCESS_KEY'),
                    'MSM_S3_BUCKET': os.getenv('MSM_S3_BUCKET'),
                    'DATABASE_URL': os.getenv('DATABASE_URL')
                   }
    ec2_userdata = render_to_string('launcher/userdata.txt', ec2_env_vars)

    # Launch EC2 instance
    region = boto.ec2.get_region(ec2_region)
    conn = boto.connect_ec2(region=region)
    reservation = conn.run_instances(
                        image_id=ec2_ami,
                        key_name=ec2_keypair,
                        security_groups=ec2_secgroups,
                        instance_type=ec2_instancetype,
                        user_data=ec2_userdata)
    server = reservation.instances[0]
    while server.state == u'pending':
        time.sleep(5)
        server.update()

    # Save to DB and send notification
    instance.name = server.id
    instance.ip_address = server.ip_address
    instance.state = 'pending'
    instance.save()
    send_event('name', instance.name)
    send_event('ip_address', instance.ip_address)
    send_event('state', instance.state)

    # Send task to check if instance is running
    check_state.delay(instance_id, 'running')

    return True


@task(max_retries=60)
def check_state(instance_id, state):
    instance = Instance.objects.get(pk=instance_id)
    if instance.state == state:
        send_event('state', instance.state)
    # elif instance.state in ['initiating', 'pending', 'killing', 'shutting down']:
    else:
        check_state.retry(countdown=5)


@task
def terminate(instance_id):
    # Retrieve instance obj from DB.
    instance = Instance.objects.get(pk=instance_id)

    # Terminate instance
    ec2_region = os.getenv('MCL_EC2_REGION', 'us-west-2')
    region = boto.ec2.get_region(ec2_region)
    conn = boto.connect_ec2(region=region)
    conn.terminate_instances(instance_ids=[instance.name])

    # Save to DB and send notification
    timestamp = datetime.datetime.utcnow().replace(tzinfo=utc)
    instance.end = timestamp
    # instance.state = 'killing'
    instance.save()
    # send_event('state', 'killing')

    # Send task to check if instance has been terminated.
    check_state.delay(instance_id, 'terminated')

    return True

@task(ignore_result=True)
def sse_keepalive():
    send_event('keepalive', 'ping')
