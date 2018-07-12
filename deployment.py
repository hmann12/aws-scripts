# this script creates a new Launch Config by copying data from an existing Launch LaunchConfigurations
# it then creates a new ASG based on the newly created ASG.
# associates instances in the new ASG to a Load Balancer

from __future__ import print_function
import boto3
import sys
from dateutil import parser
import re
import json, ast
import itertools
import base64
from datetime import date
import random
import string
import time
# import start_instance

conn_session = boto3.Session(profile_name='dev')

# VARIABLES
# -----------------------------------------------------------------------
random = ''.join([random.choice(string.digits) for n in xrange(8)])
asg_names = []
asg_creation_times = []
current_lc_name = []
asg_subnets = ''
alb_names = []
alb_arn = ''
alb_arn_list = []
target_group_arn_list = []
health_status = []
target_name = []
instance_type = ''
iam_instance_profile = ''
security_groups = ''
user_data = ''
root_block_device = {}
asg_service_role = '---service role arn goes here-----'

print('STARTING THE PROGRAM')
print('vvvvvvvvvvvvvvvvvvvv')
print('\n')

# python /Users/harsh/work/platform-scripts/start_instance.py
# DESCRIBE ASG - GET LC NAME
# -----------------------------------------------------------------------
print('GET THE CURRENT ASG DETAILS')
print('---------------------------')
asg_client = conn_session.client('autoscaling', region_name='us-west-2')
asg_describe_response = asg_client.describe_auto_scaling_groups()
for asg in asg_describe_response['AutoScalingGroups']:
    asg_names.append(asg['AutoScalingGroupName'])
    asg_creation_times.append(asg['CreatedTime'].strftime("%Y-%m-%d %H:%M:%S"))
    r = re.compile('.*Frontend-Magento*')
    asg_name_regex = [x for x in asg_names if r.match(x)]
    all_asg = dict(zip(asg_names, asg_creation_times))
    for key, value in all_asg.iteritems():
        asg_regex = {key:value for key, value in all_asg.items() if key in asg_name_regex}
    asg_name = ''.join([k for k,v in asg_regex.iteritems() if v == max(asg_regex.values())])
    if asg['AutoScalingGroupName'] == asg_name:
        current_lc_name = asg['LaunchConfigurationName']
        asg_subnets = (asg['VPCZoneIdentifier'])
asg_vpc_zone_identifier = asg_subnets.split(',')
new_asg_name = ''.join([i for i in asg_name if not i.isdigit()]).strip('-')+'-'+str(date.today())+'-'+random
print('The current ASG name is: ' + asg_name)
print('The new ASG name will be: ' + new_asg_name)
print('\n')

# GET TARGET GROUP INFORMATION AND THE TARGET HEALTH
# -----------------------------------------------------------------------
print('TARGET GROUPS FROM THE ASG')
print('--------------------------')
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
print('Target Groups to be removed from the ASG are ' + '\n' + '\n'.join([i for i in target_group_arn_list[1:]]))
print('\n')

# GET TARGET HEALTH
# -------------------------------------------------------------------------
print('TARGET HEALTH')
print('-------------')
def target_health_status():
    for targets in target_group_arn_list:
        target_group_health_response = alb_client.describe_target_health(TargetGroupArn=targets)
        for target_health in target_group_health_response['TargetHealthDescriptions']:
            health_status.append(target_health['TargetHealth']['State'])
            target_name.append(target_health['Target']['Id'])
    d = dict(zip(target_name, health_status))
    return d

print(target_health_status())
print('\n')

# DETACH TARGET GROUPS
# -----------------------------------------------------------------------
print('DETACHING THE TARGET GROUPS')
print('---------------------------')
print('You really wish to continue, this cannot be undone ? Please enter (Yes/No):')
choice = raw_input().upper()
print('> ', end='')
if ((choice == 'Y') or (choice == 'YES')):
    try:
        asg_update_response = asg_client.detach_load_balancer_target_groups(
            AutoScalingGroupName=asg_name,
            TargetGroupARNs=target_group_arn_list[1:]
        )
        print('The Target Groups have been detached')
    except Exception as e:
        print('Removing Targets from the current ASG Failed: ' + str(e))
        exit()
    print('\n')
else:
    print('No option selected or option invalid, please re-run the program')
    exit()



# DESCRIBE LC - GET DETAILS
# -----------------------------------------------------------------------
print('GET THE CURRENT LC')
print('------------------')
lc_describe_response = asg_client.describe_launch_configurations()
for LC in lc_describe_response['LaunchConfigurations']:
    if LC['LaunchConfigurationName'] == current_lc_name:
        instance_type = LC['InstanceType']
        iam_instance_profile = LC['IamInstanceProfile']
        security_groups = LC['SecurityGroups']
        user_data = LC['UserData']
        root_block_device=(LC['BlockDeviceMappings'])

user_data_decoded = base64.b64decode(user_data)
new_lc_name = ''.join([i for i in current_lc_name if not i.isdigit()])+str(date.today())
print('The new LC name will be ' + new_lc_name)
print('\n')

# CREATE NEW LC - FROM THE ABOVE DETAILS
# -----------------------------------------------------------------------
print('CREATING THE NEW LC')
print('-------------------')
print('Are you sure you want to create the new LC - ' + new_lc_name + ' ' + '(YES/NO) ?')
lc_choice = raw_input().upper()
print('> ', end='')
if ((lc_choice == 'Y') or (lc_choice == 'YES')):
    try:
        lc_create_response = asg_client.create_launch_configuration(
            LaunchConfigurationName=new_lc_name,
            ImageId='ami-0e8370f014290a8f8',
            InstanceType=instance_type,
            IamInstanceProfile=iam_instance_profile,
            SecurityGroups=security_groups,
            UserData=user_data_decoded,
            BlockDeviceMappings=root_block_device
        )
        print('New LC Created -', new_lc_name)
    except Exception as e:
        print('LC Creation Failed ' + str(e))
        exit()
    print('\n')
else:
    print('No option selected or option invalid')
    print('Please run the program again')
    exit()


# CREATE ASG
# -----------------------------------------------------------------------
print('CREATING THE NEW ASG')
print('--------------------')
print('Are you sure you want to create the new ASG (YES/NO) ?')
asg_choice = raw_input().upper()
print('> ', end='')
if ((lc_choice == 'Y') or (lc_choice == 'YES')):
    try:
        asg_creation_response = asg_client.create_auto_scaling_group(
            AutoScalingGroupName=new_asg_name,
            LaunchConfigurationName=new_lc_name,
            MinSize=0,
            MaxSize=10,
            DesiredCapacity=3,
            DefaultCooldown=300,
            TargetGroupARNs=target_group_arn_list[1:],
            HealthCheckType='EC2',
            HealthCheckGracePeriod=300,
            ServiceLinkedRoleARN=asg_service_role,
            VPCZoneIdentifier=','.join(asg_vpc_zone_identifier)
        )
    except Exception as e:
        print('ASG Creation Failed: ' + str(e))
        exit()
    print('Viola! New Infrastructure is ready')
    print('PLEASE MAKE SURE YOU CHECK IF THEY ARE HEALTHY')
    print('\n')
else:
    print('No option selected or option invalid')
    print('Please run the program again')
    exit()
