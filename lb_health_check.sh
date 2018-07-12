#!/bin/bash
WEB_TIER_URL='http://localhost/health_check.php'
APP_TIER_URL='http://localhost/healthcheck/'

# using the right AWS profile
AWS_CLI_BIN=$(which aws)
AWS_CLI="${AWS_CLI_BIN} --region us-west-2"

# get the Instance ID used to set the status if found unhealthy
INST_ID=$(wget -q -O - http://169.254.169.254/latest/meta-data/instance-id)

ENVIRONMENT='{{ NAME_ENV }}'
AWS_ACNT_NUMBER='{{ ACCOUNT_NUMBER }}'
SNS_ARN='{{ SNS_TOPIC }}'

# Database details
DB_HOST='{{ DB_RW_ENDPOINT }}'
DB_USER='{{ DB_USERNAME }}'
DB_NAME='{{ DB_NAME }}'
DB_PASS='{{ DB_PASSWORD }}'
SQL_QUERY="select 1;"

# Redis details
REDIS_PRIMARY='{{ REDIS_DEFAULT_ENDPOINT }}'
REDIS_FPC='{{ REDIS_FPC_ENDPOINT }}'
REDIS_SESSION='{{ REDIS_SESSION_ENDPOINT }}'
redis=(${REDIS_PRIMARY} ${REDIS_FPC} ${REDIS_SESSION}) # arary of Redis endpoints, used later to ping and check connectivity

COUNTER=0
THRESHOLD=3

# curl the web tier health check
web_status=$(curl --write-out %{http_code} --silent --output /dev/null ${WEB_TIER_URL})

function health_check_thrice() {
  while true; do
    $1
    if [ $? -eq 0 ]; then
      return 0
    elif [ "$COUNTER" -gt "$THRESHOLD" ]; then
      return 1
    else
      sleep 5
      COUNTER=$((COUNTER+1))
    fi
  done
}

function health_check() {
  web_status=$(curl --write-out %{http_code} --silent --output /dev/null ${WEB_TIER_URL})
  if [ ${web_status} -eq 200 ]; then
    app_status=$(curl -H "X-Forwarded-Proto: https" --write-out %{http_code} --silent --output /dev/null ${APP_TIER_URL})
    if [ ${app_status} -ne 200 ]; then
      mysql -h ${DB_HOST} -u ${DB_USER} -p${DB_PASS} ${DB_NAME} -e "${SQL_QUERY}" &> /dev/null
      if [ $? -ne 0 ]; then
        ${AWS_CLI} sns publish --topic-arn "${SNS_ARN}" --subject "${ENVIRONMENT}-Magento Healthcheck Failing" --message "${ENVIRONMENT} Database Connection Failure for ${INST_ID}" &> /dev/null
        return 1
      fi
      for i in "${redis[@]}"
      do
        REDIS_STATUS=$(redis-cli -h ${i} PING)
        if [ "${REDIS_STATUS}" != "PONG" ]; then
          ${AWS_CLI} sns publish --topic-arn "${SNS_ARN}" --subject "${ENVIRONMENT}-Magento Healthcheck Failing" --message "${ENVIRONMENT} Redis Faliure - Unable to connect to ${i} - for ${INST_ID}" &> /dev/null
          return 1
        fi
      done
      DISK=$(df -h | grep -o '/dev.*%' | awk '{ print $5 }' | tr --delete %)
      if [ "${DISK}" -gt "95" ]; then
        ${AWS_CLI} sns publish --topic-arn "${SNS_ARN}" --subject "${ENVIRONMENT}-Magento Healthcheck Failing" --message "${ENVIRONMENT} Disk Full or above Threshold - 95% - for ${INST_ID}" &> /dev/null
        return 1
      fi
      ${AWS_CLI} sns publish --topic-arn "${SNS_ARN}" --subject "${ENVIRONMENT}-Magento Healthcheck Failing" --message "${ENVIRONMENT} Application Tier Health Check is Failing for ${INST_ID}" &> /dev/null
      return 1
    else
      return 0
    fi
  else
    ${AWS_CLI} sns publish --topic-arn "${SNS_ARN}" --subject "${ENVIRONMENT}-Magento Healthcheck Failing" --message "${ENVIRONMENT} Web Tier Health Check is Failing for ${INST_ID}" &> /dev/null
    return 1
  fi
}

STARTUP_SCRIPT_STATUS=$(systemctl status template-on-startup | grep -o "Main PID: [0-9]\+ (code=exited, status=[0-9]\+" | grep -o "code=exited, status=[0-9]\+" | grep -o "[0-9]\+")
if [ ${STARTUP_SCRIPT_STATUS} -ne 0 ]; then
  ${AWS_CLI} sns publish --topic-arn "${SNS_ARN}" --subject "${ENVIRONMENT}-Start Up Script Failed" --message "${ENVIRONMENT} Start Up Script Failinig - ${INST_ID}" &> /dev/null
  exit 1
else
  health_check_thrice health_check;
  if [ $? -ne 0 ]; then
    ${AWS_CLI} sns publish --topic-arn "${SNS_ARN}" --subject "${ENVIRONMENT}-Magento Healthcheck Failing" --message "${ENVIRONMENT} Health Check Failed - Terminating the Instance ${INST_ID}" &> /dev/null
    ${AWS_CLI} autoscaling set-instance-health --instance-id ${INST_ID} --health-status Unhealthy &> /dev/null
    exit 1
  else
    exit 0
  fi
fi
