"""
A troposphere module for generating an AWS cloudformation template
defining a VPC Flow Logs configuration.
"""

import sys
from troposphere import (
    GetAtt,
    Join,
    Output,
    Ref,
    iam,
    logs,
    ec2,
)
from troposphere.iam import Policy as TropoPolicy
from awacs.aws import (
    Statement,
    Policy,
)
import awacs
import awacs.logs

from sceptremods.templates import BaseTemplate
from sceptremods.util.policies import flowlogs_assumerole_policy


#
# Globals
#

ALLOWED_TRAFFIC_TYPES = ["ACCEPT", "REJECT", "ALL"]
JOINED_TRAFFIC_TYPES = '/'.join(ALLOWED_TRAFFIC_TYPES)
CLOUDWATCH_ROLE_NAME = "Role"
FLOW_LOG_GROUP_NAME = "LogGroup"
FLOW_LOG_STREAM_NAME = "LogStream"
LOG_RETENTION_VALUES = [
    0, 1, 3, 5, 7, 14, 30, 60, 90, 120, 150,
    180, 365, 400, 545, 731, 1827, 3653
]


#
# sceptre_user_data validation functions
#

def validate_cloudwatch_log_retention(value):
    if value not in LOG_RETENTION_VALUES:
        raise ValueError(
            "%d is not a valid retention period. Must be one of: %s" % (
                value,
                str(LOG_RETENTION_VALUES)
            )
        )
    return value


def validate_traffic_type(traffic_type):
    if traffic_type not in ALLOWED_TRAFFIC_TYPES:
        raise ValueError(
            "Traffic type must be one of the following: {}".format(
             '/'.join(ALLOWED_TRAFFIC_TYPES))
        )

    return traffic_type


#
# scepter_user_date variable specifications
#

VARSPEC = {
    "Retention": {
        "type": int,
        "description": "Time in days to retain Cloudwatch Logs. Accepted "
                       "values: {}.".format(str(LOG_RETENTION_VALUES)),
        #"default": 0,
        "default": 1,
        "validator": validate_cloudwatch_log_retention,
    },
    "VpcId": {
        "type": str,
        "description": "ID of the VPC in which to enable flow logs.",
        "default": "bogus-VpcId-for-testing-only",
    },
    "TrafficType": {
        "type": str,
        "description": "Type of traffic to log. Must be one of the "
                       "following: {}".format('/'.join(ALLOWED_TRAFFIC_TYPES)),
        "default": "ALL",
        "validator": validate_traffic_type,
    },
    'Tags': {
        'type': dict,
        'default': dict(),
        'description': (
"""Dictionary of tags to apply to stack resources (e.g. {tagname: value})"""),
    },
}


#
# this should get moved somewhere else
#
def vpc_flow_log_cloudwatch_policy(log_group_arn):
    return Policy(
        Statement=[
            Statement(
                Effect="Allow",
                Action=[
                    awacs.logs.DescribeLogGroups
                ],
                Resource=["*"],
            ),
            Statement(
                Effect="Allow",
                Action=[
                    awacs.logs.CreateLogStream,
                    awacs.logs.DescribeLogStreams,
                    awacs.logs.PutLogEvents,
                ],
                Resource=[
                    log_group_arn,
                    Join('', [log_group_arn, ":*"]),
                ],
            ),
        ]
    )


class FlowLogs(BaseTemplate):

    def create_template(self):
        t = self.template
        variables = self.validate_user_data()

        self.log_group = t.add_resource(
            logs.LogGroup(
                FLOW_LOG_GROUP_NAME,
                RetentionInDays=variables["Retention"],
            )
        )

        t.add_output(
            Output(
                "%sName" % FLOW_LOG_GROUP_NAME,
                Value=Ref(self.log_group)
            )
        )
        t.add_output(
            Output(
                "%sArn" % FLOW_LOG_GROUP_NAME,
                Value=GetAtt(self.log_group, "Arn")
            )
        )

        self.role = t.add_resource(
            iam.Role(
                CLOUDWATCH_ROLE_NAME,
                AssumeRolePolicyDocument=flowlogs_assumerole_policy(),
                Path="/",
                Policies=[
                    TropoPolicy(
                        PolicyName="vpc_cloudwatch_flowlog_policy",
                        PolicyDocument=vpc_flow_log_cloudwatch_policy(
                            GetAtt(self.log_group, "Arn")
                        ),
                    ),
                ]
            )
        )

        t.add_output(
            Output(
                "%sName" % CLOUDWATCH_ROLE_NAME,
                Value=Ref(self.role)
            )
        )
        role_arn = GetAtt(self.role, "Arn")
        t.add_output(
            Output(
                "%sArn" % CLOUDWATCH_ROLE_NAME,
                Value=role_arn
            )
        )

        self.log_stream = t.add_resource(
            ec2.FlowLog(
                FLOW_LOG_STREAM_NAME,
                DeliverLogsPermissionArn=role_arn,
                LogGroupName=Ref(FLOW_LOG_GROUP_NAME),
                ResourceId=variables["VpcId"],
                ResourceType="VPC",
                TrafficType=variables["TrafficType"],
            )
        )

        t.add_output(
            Output(
                "%sName" % FLOW_LOG_STREAM_NAME,
                Value=Ref(self.log_stream)
            )
        )


#
# The sceptre handler
#
def sceptre_handler(sceptre_user_data):
    flow_logs = FlowLogs(sceptre_user_data, VARSPEC)
    flow_logs.create_template()
    return flow_logs.template.to_json()

def main():
    if len(sys.argv) > 1:
        flow_logs = FlowLogs(None, VARSPEC)
        flow_logs.help(flow_logs)
    else:
        print(sceptre_handler(dict()))
    

if __name__ == '__main__':
    main()
