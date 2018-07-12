# script to get the health status of instance behind an alb

import boto3
import sys
from dateutil import parser
import re
import json, ast
import itertools
import base64
import time
from collections import defaultdict

conn_session = boto3.Session(profile_name='dev')

# GET TARGET GROUP INFORMATION
alb_client = conn_session.client('elbv2', region_name='us-west-2')
alb_names = []
alb_arn = ''
alb_arn_list = []
target_group_arn_list = []
health_status = []
target_name = []

alb_client = conn_session.client('elbv2', region_name='us-west-2')

alb_describe_response = alb_client.describe_load_balancers()
for alb in alb_describe_response['LoadBalancers']:
    alb_names.append(alb['LoadBalancerName'])
    r = re.compile('.*Magento-External*')
    alb_name = ''.join([x for x in alb_names if r.match(x)])
    if alb['LoadBalancerName'] == alb_name:
        alb_arn = alb['LoadBalancerArn']
        alb_arn_list.append(alb_arn)
target_group_response = alb_client.describe_target_groups()
for target in target_group_response['TargetGroups']:
    if target['LoadBalancerArns'] == alb_arn_list:
        target_group_arn_list.append(target['TargetGroupArn'])

for targets in target_group_arn_list[1:]:
    target_group_health_response = alb_client.describe_target_health(TargetGroupArn=targets)
    for target_health in target_group_health_response['TargetHealthDescriptions']:
        health_status.append(target_health['TargetHealth']['State'])
        target_name.append(target_health['Target']['Id'])
for x,y in zip(target_name, health_status):
    print x, y
