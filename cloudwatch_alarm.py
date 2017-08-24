# this program fetches metric information from CloudWatch and sets up alarms based on that information
# for example fetch the autoscaling group information from system/linux metrics in cloudwatch
# and set up alarms that notifies SNS topic which further triggers
# a lambda function

import boto3
cloudwatch = boto3.client('cloudwatch')

auto_group_name = []
paginator = cloudwatch.get_paginator('list_metrics')
for response in paginator.paginate(Dimensions=[{'Name': 'AutoScalingGroupName'}],
                                   MetricName='DiskSpaceUtilization',
                                   Namespace='System/Linux'):
    data = response['Metrics']
for i in data:
    dimension = i['Dimensions']
    for i in dimension:
        if i['Name'] == 'AutoScalingGroupName':
            auto_group_name.append(i['Value'])

for i in auto_group_name:
    cloudwatch.put_metric_alarm(
        AlarmName='-'.join(i.split('-')[:2])+'-'+'root'+'-'+'diskspace',
        ComparisonOperator='GreaterThanThreshold',
        EvaluationPeriods=1,
        MetricName='DiskSpaceUtilization',
        Namespace='System/Linux',
        Period=300,
        Statistic='Maximum',
        Threshold=80.0,
        ActionsEnabled=True,
        AlarmActions=[
            '------sns topic goes here----'
        ],
        OKActions=[
            '------sns topic goes here----'
        ],
        InsufficientDataActions=[
            '------sns topic goes here----'
        ],
        AlarmDescription='Alarm when server disk exceeds 80%',
        Dimensions=[
            {
            'Name': 'Filesystem',
            'Value': '/dev/xvda1',
            },
            {
            'Name': 'MountPath',
            'Value': '/',
            },
            {
            'Name': 'AutoScalingGroupName',
            'Value': i
            }
        ],
    )
