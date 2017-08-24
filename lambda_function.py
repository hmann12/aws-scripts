# this aws lambda function when triggered by an SNS topic posts output on to a slack channel
# for example here this function is printing out the output of various disk space alarms set up in cloudwatch

from __future__ import print_function

import boto3
import json
import logging
import re

from urllib2 import Request, urlopen, URLError, HTTPError

HOOK_URL = '--------slack-webhook-url-goes-here-----------------'

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("Event: " +  str(event))

    color = "good" # "danger" or "warning"
    record = event['Records'][0]
    logger.info("Record: " +  str(record))

    message = record['Sns']['Message']
    logger.info("Message: " + message)
    jsonmessage = json.loads(message)

    AlarmName = jsonmessage['AlarmName']
    NewStateValue = jsonmessage['NewStateValue']
    x = jsonmessage['NewStateReason']
    parse = str(x.split(':')[1:])
    num = parse[parse.index("[") + 1:parse.rindex("]")].split("[")[1].split(' ')[:1]
    result = str(map(float, num))
    num_rounded = round(float(result[1:-1]),2)
    NewStateReason = re.sub(str(num[0]), str(num_rounded), x)

    toslack = NewStateValue + ": " + AlarmName + " " + NewStateReason
    logger.info("ToSlack: " + toslack)

    #send critical messages to #alert-watcher slack room
    channel = '#aws-monitoring'
    if NewStateValue == 'ALARM' :
        color = "danger"
    logger.info("Color: " + color)

    attachments = [
        {
          "text": "%s" % (toslack),
          "color" : color,
        }
    ]

    slack_message = {
        "username": "cloudwatch",
        "channel": channel,
        "icon_emoji": ":cloudwatch:",
        "attachments": attachments
    }

    req = Request(HOOK_URL, json.dumps(slack_message))
    try:
        response = urlopen(req)
        response.read()
        logger.info("Message posted to slack channel")
    except HTTPError as e:
        logger.error("Request failed: %d %s", e.code, e.reason)
    except URLError as e:
        logger.error("Server connection failed: %s", e.reason)
