#!/usr/bin/env bash

# Runs puppet cert list --all
# Iterates over all lines in the output
# Looks for cert names like: server-name-ip-xx-xx-xx-xx.us-west-2.compute.internal
# Checks to see if those instances exist using the AWS CLI
# If not, remove the cert.

for cert_name in `puppet cert list --all | grep '^+ ' | awk '{print $2}' | sed 's/"//g' | grep '[a-zA-Z]\+-[a-zA-Z]\+-ip-172-16-[0-9]\+-[0-9]\+.us-west-2.compute.internal'`; do
    private_dns=`echo $certname | sed 's#.*\(ip.*\)#\1#'`
    status=`aws ec2 describe-instances --filters Name=private-dns-name,Values=${private_dns} --query 'Reservations[*].Instances[*].{State:State.Name}' --region us-west-2`
    if [ "$status" == "[]" ] ; then
        puppet cert clean ${cert_name}
        puppet node deactivate ${cert_name}
        puppet node clean ${cert_name}
    fi
done
