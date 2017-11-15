# Scripts to manage AWS services

* [Cloudwatch Alarm](https://github.com/hmann12/aws-scripts/blob/master/cloudwatch_alarm.py) Script to create cloudwatch alarm to monitor disk space utilization for servers in an Autoscaling group.
* [EC2 and RDS Status](https://github.com/hmann12/aws-scripts/blob/master/ec2_rds_status.py) Fetch the status of EC2 and RDS instances and send out notifications to appropriate Slack channels.
* [AWS Lambda Function](https://github.com/hmann12/aws-scripts/blob/master/lambda_function.py) Lambda function when triggered by an SNS topic post notifications to slack channels. SNS is triggered by CloudWatch alarms.
