import boto.ec2
import boto
import boto3.session
import re
from datetime import datetime
import requests
import json

now = datetime.now()  # current time
night_begin = now.replace(hour=0, minute=0, second=0, microsecond=0) # time 12am
night_end = now.replace(hour=4, minute=0, second=0, microsecond=0)   # time 4am
red = 'danger'
green = '#32CD32'
orange = '#FF6347'
channel = '---slack channel name---'   # Enter your slack-channel name
slack_url = '---slack webhook URL---' # your slack webhook url

def post_to_slack(ec2_status, ec2_color, rds_status, rds_color):
    ec2_payload = {"channel": channel, "username": "EC2 Instance Status", "attachments": [{"text": ec2_status, "color": ec2_color}]}
    rds_payload = {"channel": channel, "username": "RDS Instance Status", "attachments": [{"text": rds_status, "color": rds_color}]}
    headers = {'Content-type': 'application/json'}
    ec2_response = requests.post(slack_url, data=json.dumps(ec2_payload), headers=headers)
    rds_response = requests.post(slack_url, data=json.dumps(rds_payload), headers=headers)


def get_ec2_status():
    region_name = next(x for x in boto.ec2.regions() if x.name=='---region name goes here---')
    conn = boto.ec2.EC2Connection(profile_name='--profile name goes here--', region=region_name)    # aws profile in credentials and region name
    reservations = conn.get_all_instances()
    array = []
    for res in reservations:
        for inst in res.instances:
            if 'Name' in inst.tags and re.search('temp-mysql', inst.tags['Name']):   # search for specific instances by name in this case temp-mysql
                array.append(inst.state)
    if not array:
        ec2_status = "There are NO temp instances"
        ec2_color = red
    else:
        if now >= night_begin and now <= night_end:
            if array.count('stopped') > 0:
                ec2_status = 'There are %s temp EC2 instances STOPPED' % array.count('stopped')
                ec2_color = red
            else:
                ec2_status = "All temp EC2 instances are RUNNING"
                ec2_color = green
        else:
            if array.count('running') > 0:
                ec2_status = "There are %s temp EC2 instances RUNNING" % array.count('running')
                ec2_color = red
            else:
                ec2_status = "All temp EC2 instances are STOPPED"
                ec2_color = green
    return ec2_status, ec2_color

def get_rds_status():
    session = boto3.Session(profile_name='--profile name goes here--')   # aws credentials
    rds = session.client('rds')
    if now >= night_begin and now <= night_end:
        try:
            dbs = rds.describe_db_instances(DBInstanceIdentifier='temp-min')   # checking RDS instance named temp-min
            if dbs['DBInstances'][0]['DBInstanceStatus'] == 'available':
                rds_status = 'The RDS temp instance is RUNNING'
                rds_color = green
            else:
                rds_status = 'The RDS temp instance is ' + dbs['DBInstances'][0]['DBInstanceStatus']
                rds_color = orange
        except Exception as error:
            rds_status = 'The RDS temp instance does not exist'
            rds_color = red
    else:
        try:
            dbs = rds.describe_db_instances(DBInstanceIdentifier='temp-min')
            if dbs['DBInstances'][0]['DBInstanceStatus'] == 'available':
                rds_status = 'The RDS temp instance is RUNNING'
                rds_color = red
            else:
                rds_status = 'The RDS temp instance is ' + dbs['DBInstances'][0]['DBInstanceStatus']
                rds_color = orange
        except Exception as error:
            rds_status = 'The RDS temp instance does not exist'
            rds_color = green
    return rds_status, rds_color

def main():
    ec2_status, ec2_color = get_ec2_status()
    rds_status, rds_color = get_rds_status()
    post_to_slack(ec2_status, ec2_color, rds_status, rds_color)


if __name__ == '__main__':
    main()
