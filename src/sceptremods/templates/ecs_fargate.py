"""
Assumptions:
    using fargate
    using ALB 
    only one publicly available port
    one service, one task, one container
    no task volumes
"""

import sys

from troposphere import (
    NoValue,
    AccountId,
    Region,
    GetAtt,
    Join,
    Output,
    Ref,
)
from troposphere import (
    ecs,
    logs,
    route53,
)
import troposphere.elasticloadbalancingv2 as elb

from sceptremods.util.acm import get_elb_hosted_zone_id
from sceptremods.templates import BaseTemplate


#
# The template class
#
class ECSFargate(BaseTemplate):

    VARSPEC = {

        # ECS service vars
        'VpcId': {
            'type': str,
            #'default': 'bogus-VpcId-for-testing-only',
            'description': 'ID of the VPC to use for ecs service.',
        },
        'Subnets': {
            'type': str,
            'default': str(),
            'description': 'A comma sepatrated list of VPC private subnet IDs to use for this ECS service.',
            #'validator': comma_separated_values,
        },
        'SecurityGroup': {
            'type': str,
            'default': str(),
            'description': 'Name of the VPC security group to use for this service.',
        },
        'ClusterName': {
            'type': str,
            'default': 'default',
            'description': 'Name of an ECS cluster to use.',
        },
        'DesiredCount': {
            'type': int,
            'default': 1,
            'description': 'The number of task instances to run on the cluster.',
        },

        # ECS task vars
        'Cpu': {
            'type': int,
            'default': 256,
            'description': 'The number of cpu units used by the task.  Must be one of [256, 512, 1024, 2048, 4096].',
        },
        'Memory': {
            'type': int,
            'default': 512,
            'description': 'The amount (in MiB) of memory used by the task.',
        },
        'Family': {
            'type': str,
            'default': str(),
            'description': 'The name of a family that this task definition is registered to.  If not specified, use the container name.',
        },
        'LogRetention': {
            'type': int,
            'default': 14,
            'description': 'Number of days to retain cloudwatch logs.',
        },
        'TaskRoleArn': {
            'type': str,
            'default': str(),
            'description': 'ARN of an IAM role to accociate with the ECS task.',
        },

        # ECS container vars
        'ContainerName': {
            'type': str,
            'default': str(),
            'description': 'The name of the ECS container.',
        },
        'ContainerPort': {
            'type': int,
            'default': 80,
            'description': 'The port number on the ECS container.',
        },
        'ContainerProtocol': {
            'type': str,
            'default': 'tcp',
            'description': 'The network protocol of the ECS container.',
        },
        'ContainerImage': {
            'type': str,
            'default': str(),
            'description': 'The name of the docker image to use for the ECS container.',
        },
        'ContainerImageVersion': {
            'type': str,
            'default': 'latest',
            'description': 'The docker image version to use for the ECS container.',
        },
        'UseECR': {
            'type': bool,
            'default': False,
            'description': 'Whether or not the container image repository is in ECR.  When "True" the ContainerName var is expanded into a ECR path based on the account id and region.',
        },
        'AdditionalContainerAttributes': {
            'type': dict,
            'default': dict(),
            'description': 'Dictionary of additional attributes to apply to the container definition.  See Cloudformation Docs for ECS Tasks for available attributes and syntax.',
        },

        # ALB listener vars
        'LoadBalancerArn': {
            'type': str,
            'default': str(),
            'description': 'ARN of the AWS application loadbalancer to use for this service.',
        },
        'LoadBalancerUrl': {
            'type': str,
            'default': str(),
            'description': 'URL of the ALB.',
        },
        'DefaultListener': {
            'type': str,
            'default': str(),
            'description': 'ARN of the default listener associated with the ALB.',
        },
        'ListenerPort': {
            'type': int,
            'default': 80,
            'description': 'The network port of the ALB Listener.',
        },
        'TargetGroupProtocol': {
            'type': str,
            'default': 'HTTP',
            'description': 'The protocol of the target group.  Either HTTP or HTTPS.',
        },
        'HealthCheckAttributes': {
            'type': dict,
            'default': dict(),
            'description': 'Dictionary of ELB target group health check attributes.  See Cloudformation Docs on ELB target groups for available attributes and syntax.',
        },
        'Certificates': {
            'type': list,
            'default': list(),
            'description': 'A list of ssl certs to attach to the ALB listener for this service.',
        },
        'HostedZone': {
            'type': str,
            'default': str(),
            'description': 'AWS hosted zone domain name.',
        },
        'ServiceFqdn': {
            'type': str,
            'default': str(),
            'description': 'The fully qualified DNS name to use for the service.  This becomes a CNAME to the ALB in route53.  Leave blank if you do not require a DNS name for this service.',
        },
    }


    def munge_container_attributes(self):
        image =':'.join([
            self.vars['ContainerImage'], 
            self.vars['ContainerImageVersion'],
        ])
        # munge ECR image path
        if self.vars['UseECR']:
            image = Join('.', [AccountId, 'dkr.ecr', Region, 'amazonaws.com/' + image])
        # set required attributes
        required = dict(
            Name=self.vars['ContainerName'],
            Image=image,
            PortMappings=[ecs.PortMapping(
                ContainerPort=self.vars['ContainerPort'],
                Protocol=self.vars['ContainerProtocol'],
            )],
            LogConfiguration=ecs.LogConfiguration(
                LogDriver='awslogs',
                Options={
                    'awslogs-group': Ref(self.log_group),
                    'awslogs-region': Region,
                    'awslogs-stream-prefix': self.vars['ContainerName'],
                },
            ),
        )
        # deal with additional attributes
        if self.vars['AdditionalContainerAttributes']:
            added = self.vars['AdditionalContainerAttributes']
            # deal with troposphere AWSProperty objects
            if 'Environment' in added:
                added['Environment'] = [
                    ecs.Environment(**m) for m in added['Environment']
                ]
            if 'ExtraHosts' in added:
                added['ExtraHosts'] = [
                    ecs.HostEntry(**m) for m in added['ExtraHosts']
                ]
            if 'LinuxParameters' in added:
                added['LinuxParameters'] = [
                    ecs.LinuxParameters(**m) for m in added['LinuxParameters']
                ]
            if 'MountPoints' in added:
                added['MountPoints'] = [
                    ecs.MountPoint(**m) for m in added['MountPoints']
                ]
            if 'Ulimit' in added:
                added['Ulimit'] = [
                    ecs.Ulimit(**m) for m in added['Ulimit']
                ]
            if 'VolumesFrom' in added:
                added['VolumesFrom'] = [
                    ecs.VolumesFrom(**m) for m in added['VolumesFrom']
                ]
            # munge memory
            if not 'Memory' in added and not 'MemoryReservation' in added:
                added['MemoryReservation'] = self.vars['Memory']

            attributes  = added.copy()
        else:
            attributes = dict()

        # merge in required attributes.
        attributes.update(required)
        return attributes


    def create_log_group(self):
        t = self.template
        log_group = t.add_resource(logs.LogGroup(
            'LogGroup',
            LogGroupName='-'.join(['FargateLogGroup', self.vars['Family']]),
            RetentionInDays=self.vars['LogRetention'],
        ))
        return log_group


    def create_target_group(self):
        t = self.template
        required_attributes = dict(
            Port=self.vars['ContainerPort'],
            Protocol=self.vars['TargetGroupProtocol'],
            TargetType='ip',
            VpcId=self.vars['VpcId'],
        )
        if self.vars['HealthCheckAttributes']:
            if 'Matcher' in self.vars['HealthCheckAttributes']:
                self.vars['HealthCheckAttributes']['Matcher'] = elb.Matcher(
                    **self.vars['HealthCheckAttributes']['Matcher']
                )
            tg_attributes = self.vars['HealthCheckAttributes'].copy()
        else:
            tg_attributes = dict()
        tg_attributes.update(required_attributes)
        return t.add_resource(elb.TargetGroup("TargetGroup", **tg_attributes))


    def create_listener_rule(self):
        t = self.template
        listener_rule = t.add_resource(elb.ListenerRule(
            "ListenerRule",
            ListenerArn=self.vars['DefaultListener'],
            Priority=1,
            Actions=[elb.Action(
                Type="forward",
                TargetGroupArn=Ref(self.target_group)
            )],
            Conditions=[elb.Condition(
                Field="path-pattern",
                Values=['/'],
            )],
        ))
        return listener_rule

            
    def create_listener(self):
        t = self.template
        listener = t.add_resource(elb.Listener(
            "Listener",
            Port=self.vars['ListenerPort'],
            Protocol=self.protocol,
            LoadBalancerArn=self.vars['LoadBalancerArn'],
            DefaultActions=[elb.Action(
                Type="forward",
                TargetGroupArn=Ref(self.target_group)
            )],
            Certificates=[
                elb.Certificate(CertificateArn=cert_arn)
                for cert_arn in self.vars['Certificates']
            ],
        ))
        return listener


    def create_ecs_task(self):
        t = self.template
        if not self.vars['TaskRoleArn']:
            self.vars['TaskRoleArn'] = NoValue
        task_definition = t.add_resource(ecs.TaskDefinition(
            'TaskDefinition',
            RequiresCompatibilities=['FARGATE'],
            Family=self.vars['Family'],
            Cpu=str(self.vars['Cpu']),
            Memory=str(self.vars['Memory']),
            NetworkMode='awsvpc',
            ExecutionRoleArn=Join('', [
                'arn:aws:iam::', 
                AccountId, 
                ':role/ecsTaskExecutionRole'
            ]),
            TaskRoleArn=self.vars['TaskRoleArn'],
            ContainerDefinitions=[
                ecs.ContainerDefinition(**self.munge_container_attributes())
            ],
        ))
        return task_definition


    def create_ecs_service(self):
        t = self.template
        t.add_resource(ecs.Service(
            'FargateService',
            DependsOn=self.listener.title,
            Cluster=self.vars['ClusterName'],
            DesiredCount=self.vars['DesiredCount'],
            TaskDefinition=Ref(self.task_definition),
            LaunchType='FARGATE',
            NetworkConfiguration=ecs.NetworkConfiguration(
                AwsvpcConfiguration=ecs.AwsvpcConfiguration(
                    Subnets=[s.strip() for s in self.vars['Subnets'].split(',')],
                    SecurityGroups=[self.vars['SecurityGroup']],
                )
            ),
            LoadBalancers=[
                ecs.LoadBalancer(
                    ContainerName=self.vars['ContainerName'],
                    ContainerPort=self.vars['ContainerPort'],
                    TargetGroupArn=Ref(self.target_group),
                ),
            ],
        ))
        return


    def route53_record_set(self):
        t = self.template
        t.add_resource(route53.RecordSetGroup(
            "RecordSetGroup",
            HostedZoneName=self.vars["HostedZone"] + ".",
            RecordSets=[route53.RecordSet(
                Name=self.vars['ServiceFqdn'] + ".",
                Type="A",
                AliasTarget=route53.AliasTarget(
                    HostedZoneId=get_elb_hosted_zone_id(self.vars['LoadBalancerArn']),
                    DNSName=self.vars['LoadBalancerUrl'],
                ),
            )],
        ))
        return


    def create_template(self):

        # Munge user_data
        self.vars = self.validate_user_data()
        if not self.vars['Family']:
            self.vars['Family'] = self.vars['ContainerName']
        if self.vars['Certificates']:
            self.protocol = 'HTTPS'
        else:
            self.protocol = 'HTTP'
        #print(self.vars)

        # CloudWatch
        self.log_group = self.create_log_group()

        # ELB
        self.target_group = self.create_target_group()
        if self.vars['ListenerPort'] == 80:
            self.listener = self.create_listener_rule()
        else:
            self.listener = self.create_listener()

        # ECS
        self.task_definition = self.create_ecs_task()
        self.create_ecs_service()

        # Route53
        if self.vars['ServiceFqdn']:
            self.route53_record_set()
            self.service_dns = self.vars['ServiceFqdn']
        else:
            self.service_dns = self.vars['LoadBalancerUrl']

        # Outputs
        self.template.add_output(Output(
            "ServiceUrl",
            Description="The fully qualified URL of the service",
            Value='://'.join([
                self.protocol.lower(),
                self.service_dns,
            ])
        ))


#
# The sceptre handler
#
def sceptre_handler(sceptre_user_data):
    esc_service = ECSFargate(sceptre_user_data)
    esc_service.create_template()
    return esc_service.template.to_json()

def main():
    """
    When called as a script, print out the generated template.
    If any arg is supplied, call the template class help method.
    """
    if len(sys.argv) > 1:
        ECSFargate().help()
    else:
        print(sceptre_handler(dict()))

if __name__ == '__main__':
    main()
