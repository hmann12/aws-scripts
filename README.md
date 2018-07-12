# Scripts to manage AWS services

* [Cloudwatch Alarm](https://github.com/hmann12/aws-scripts/blob/master/cloudwatch_alarm.py) - script to create cloudwatch alarm to monitor disk space utilization for servers in an Autoscaling group.
* [EC2 and RDS Status](https://github.com/hmann12/aws-scripts/blob/master/ec2_rds_status.py) - fetch the status of EC2 and RDS instances and send out notifications to appropriate Slack channels.
* [AWS Lambda Function](https://github.com/hmann12/aws-scripts/blob/master/lambda_function.py) - lambda function when triggered by an SNS topic post notifications to slack channels. SNS is triggered by CloudWatch alarms.
* [Puppet Clean Old Certs/Nodes](https://github.com/hmann12/aws-scripts/blob/master/clean_old_nodes.py) - python script that will clean old nodes/certs from puppet master server.
* [BASH Script to Clean Old Puppet Certs](https://github.com/hmann12/aws-scripts/blob/master/clean_puppet_certs.sh) - bash script to clean old puppet certs.
* [BASH Script to ssh into multiple EC2 instances, tarball necessary logs and bring them down to your local](https://github.com/hmann12/aws-scripts/blob/master/get_logs.sh) - bash script to create a tarball of logs from several servers at once and bring it down to local.
* [Python Script to Start an EC2 Instance](https://github.com/hmann12/aws-scripts/blob/master/start_instance.py) - python script to start an instance based on their tag name and values.
* [Python Script to Stop an EC2 Instance](https://github.com/hmann12/aws-scripts/blob/master/stop_instance.py) - python script to stop an instance based on their tag name and values.
* [Python Script to Deploy Certain AWS Resources](https://github.com/hmann12/aws-scripts/blob/master/deployment.py) - python script to create LC, ASG and ALB.
