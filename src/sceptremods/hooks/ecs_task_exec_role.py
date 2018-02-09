# -*- coding: utf-8 -*-
from sceptre.hooks import Hook
import json
from botocore.exceptions import ClientError



class ECSTaskExecRole(Hook):
    """
    Check if the ecsTaskExecutionRole IAM role exists.  If not,
    create it and attach policy AmazonECSTaskExecutionRolePolicy.
    """

    def __init__(self, *args, **kwargs):
        super(ECSTaskExecRole, self).__init__(*args, **kwargs)

    def run(self):
        role_name = "ecsTaskExecutionRole"
        policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"

        try:
            response = self.connection_manager.call(
                service="iam",
                command="get_role",
                kwargs=dict(RoleName=role_name)
            )
            self.logger.debug("{} - Found role: {}".format(
                __name__, response["Role"]["Arn"])
            )

        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":

                policy_doc = json.dumps({
                    "Version": "2008-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {
                                "Service": "ecs-tasks.amazonaws.com"
                            },
                            "Action": "sts:AssumeRole"
                        }
                    ]
                })

                new_role = self.connection_manager.call(
                    service="iam",
                    command="create_role",
                    kwargs=dict(
                        RoleName=role_name,
                        AssumeRolePolicyDocument=policy_doc,
                    )
                )["Role"]

                self.connection_manager.call(
                    service="iam",
                    command="attach_role_policy",
                    kwargs=dict(
                        RoleName=role_name,
                        PolicyArn=policy_arn,
                    )
                )

                self.logger.debug("{} - Created role: {}".format(
                    __name__, new_role["Arn"])
                )
