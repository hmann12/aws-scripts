# Python script to start an instance based on the their Tag Value

from __future__ import print_function
import boto3
import sys
from dateutil import parser
import re
import json, ast
import itertools
import base64
from datetime import date
from botocore.exceptions import ClientError
import time

print('STARTING THE PROGRAM')
print('vvvvvvvvvvvvvvvvvvvv')
print('\n')

conn_session = boto3.Session(profile_name='dev')
ec2_client = conn_session.client('ec2', region_name='us-west-2')
stage_maintenance_id = ''
stage_maintenance_state = ''

def get_maintenance_status():
    ec2_response = ec2_client.describe_instances(Filters=[{
        'Name': 'tag:Name',
        'Values': ['Stage-Maintenance']
    }])
    for instances in ec2_response['Reservations']:
        for instance in instances['Instances']:
            server_id = instance['InstanceId']
            server_state = instance['State']['Name']
    return server_id, server_state

print('GET THE INSTANCE DETAILS')
print('------------------------')

try:
    stage_maintenance_id = get_maintenance_status()[0]
    stage_maintenance_state = get_maintenance_status()[1]
    print('Stage Maintenance ID: ', stage_maintenance_id)
    print('Stage Maintenance State: ', stage_maintenance_state)
    print('\n')
except Exception as e:
    print('There is an error: ' + str(e))
    exit()

if stage_maintenance_state == 'stopped':
    print('DOING A DRY RUN TO START')
    print('------------------------')
    try:
        ec2_client.start_instances(InstanceIds=[stage_maintenance_id], DryRun=True)
    except ClientError as e:
        if 'DryRunOperation' not in str(e):
            raise
    print('Okay! Dry run succeeded')
    print('\n')

    print('STARTING THE INSTANCE')
    print('---------------------')
    print('Are you sure you want to start the instance: (YES/NO) ?')
    ec2_choice = raw_input().upper()
    print('> ', end='')
    if ((ec2_choice == 'Y') or (ec2_choice == 'YES')):
        try:
            ec2_start_response = ec2_client.start_instances(InstanceIds=[stage_maintenance_id], DryRun=False)
            print(ec2_start_response)
            while True:
                print('...instance is %s' % get_maintenance_status()[1])
                time.sleep(3)
                if get_maintenance_status()[1] == 'running':
                    print('ALRIGHT...instance is %s' % get_maintenance_status()[1].upper() + ' proceed further')
                    break
        except ClientError as e:
            print('Error starting the instance: ', str(e))
            exit()
    else:
        print('Invalid option selected, please re-run the program')
        exit()
else:
    print('BUMMER, the instance is: ', stage_maintenance_state)
    exit()
