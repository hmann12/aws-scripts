#!/bin/bash
mkdir /home/ec2-user/my_logs
for hostname in `cat ip_address_file` ; do
    ssh -i ~/.ssh/keypathhere ec2-user@${hostname} <<-EOF
        sudo su
        tar -zcf nginx.tar.gz /var/log/nginx
        tar -zcf php-fpm.tar.gz /var/log/php-fpm
        tar -zcf magento.tar.gz /var/www/html/magento/var/log
EOF
    scp -i ~/.ssh/keypathhere ec2-user@${hostname}:/home/ec2-user/nginx.tar.gz /home/ec2-user/my_logs/${hostname}-nginx.tar.gz
done
