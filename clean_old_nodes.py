#!/usr/bin/env python

# Runs puppet cert list --all
# Iterates over all lines in the output
# Looks for cert names like: server-name-ip-xx-xx-xx-xx.us-west-2.compute.internal
# Checks to see if those instances exist using the AWS CLI
# If not, remove the cert.

import re
import boto3
from subprocess import Popen, PIPE

session = boto3.Session(profile_name='prod')
ec2 = session.resource('ec2')


def get_all_certs():
    ips = []
    p = Popen(['puppet cert list --all'], shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    output, error = p.communicate()
    for line in output.read().strip().splitlines():
        if 'prod' or 'test' in line:
            found = re.findall(r'(?:[\d]{1,3})\-(?:[\d]{1,3})\-(?:[\d]{1,3})\-(?:[\d]{1,3})', line)
            for match in found:
                match = match.replace('-', '.')
                ips.append(match)
    return ips


def aws_status(ip_list):
    running_ips = []
    instances = ec2.instances.all()
    for instance in instances:
        for ip in ip_list:
            if instance.private_ip_address == ip and instance.state['Name'] == 'running':
                ip = ip.replace('.', '-')
                running_ips.append(ip)
    return running_ips


def get_expired_certs(valid_ips):
    certs = []
    p = Popen(['puppet cert list --all'], shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    output, error = p.communicate()
    for valid_ip in valid_ips:
        if valid_ip not in output:
            certs.append(re.findall('"([^"]*)"', output))
    return certs


def delete_certs(certificate_list):
    for certificate in certificate_list:
        cmd = ('puppet cert clean {0}; puppet node deactivate {0}; puppet node clean {0}'.format(certificate))
        p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output, error = p.communicate()


running_instances_ip = aws_status(get_all_certs())
expired_certs = get_expired_certs(running_instances_ip)
delete_certs(expired_certs)

