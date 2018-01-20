"""
Assumptions:
    using fargate
    using ALB 
    only one publicly available port
    one service, one task, one container
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
        # service vars
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
            'description': 'The name of a family that this task definition is registered to.  If not specified, use the container name',
        },
        'LogRetention': {
            'type': int,
            'default': 14,
            'description': 'Number of days to retain cloudwatch logs',
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
            'description': 'The network protocol the ECS container.',
        },
        'ContainerImage': {
            'type': str,
            'default': str(),
            'description': 'The name of the docker image to use for the ECS container.',
        },
        'UseECR': {
            'type': bool,
            'default': True,
            'description': 'Whether or not the container image repository is in ECR.  When true the template expands the ContainerName var into a ECR path.  This just simplifies variable systax',
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
        'ServiceUrl': {
            'type': str,
            'default': str(),
            'description': 'The fully qualified DNS name to use for the service.  This becomes a CNAME to the ALB in route53.  Leave blank if you do not require a DNS name for this service.',
        },
    }


    def route53_record_set(self):
        t = self.template
        LocalDNS = t.add_resource(route53.RecordSetGroup(
            "RecordSetGroup",
            HostedZoneName=self.vars["HostedZone"] + ".",
            RecordSets=[route53.RecordSet(
                Name=self.vars['ServiceUrl'] + ".",
                Type="A",
                AliasTarget=route53.AliasTarget(
                    HostedZoneId=get_elb_hosted_zone_id(self.vars['LoadBalancerArn']),
                    DNSName=self.vars['LoadBalancerUrl'],
                ),
            )],
        ))


    def munge_container_attributes(self):
        attributes = dict()
        # collect required attributes
        required = dict(
            Name=self.vars['ContainerName'],
            Image=self.vars['ContainerImage'],
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
                attributes['Environment'] = [ecs.Environment(**m) for m in added['Environment']]
            if 'ExtraHosts' in added:
                attributes['ExtraHosts'] = [ecs.HostEntry(**m) for m in added['ExtraHosts']]
            if 'LinuxParameters' in added:
                attributes['LinuxParameters'] = [ecs.LinuxParameters(**m) for m in added['LinuxParameters']]
            if 'MountPoints' in added:
                attributes['MountPoints'] = [ecs.MountPoint(**m) for m in added['MountPoints']]
            if 'Ulimit' in added:
                attributes['Ulimit'] = [ecs.Ulimit(**m) for m in added['Ulimit']]
            if 'VolumesFrom' in added:
                attributes['VolumesFrom'] = [ecs.VolumesFrom(**m) for m in added['VolumesFrom']]
            # munge memory
            if not 'Memory' in added and not 'MemoryReservation' in added:
                attributes['MemoryReservation'] = self.vars['Memory']

            # merge the rest of additional attributes
            attributes.update(added)

        attributes.update(required)
        print(attributes)
        #return attributes
        return required





    def create_template(self):
        self.vars = self.validate_user_data()
        #print(self.vars)
        t = self.template
        if not self.vars['Family']:
            self.vars['Family'] = self.vars['ContainerName']


        # ALB
        #
        if self.vars['Certificates']:
            protocol = 'HTTPS'
        else:
            protocol = 'HTTP'

        target_group = t.add_resource(elb.TargetGroup(
            "TargetGroup",
            Port=self.vars['ListenerPort'],
            #Protocol=self.vars['ListenerProtocol'],
            Protocol=protocol,
            TargetType='ip',
            VpcId=self.vars['VpcId'],
            #Name=self.vars['Family'] + '-TargetGroup',
            #HealthCheckIntervalSeconds="30",
            #HealthCheckProtocol=protocol,
            #HealthCheckTimeoutSeconds="10",
            #HealthyThresholdCount="4",
            #Matcher=elb.Matcher(HttpCode="200"),
            #UnhealthyThresholdCount="3",
        ))
    

        if self.vars['ListenerPort'] == 80:
            listener_rule = t.add_resource(elb.ListenerRule(
                "ListenerRule",
                ListenerArn=self.vars['DefaultListener'],
                Priority=1,
                Actions=[elb.Action(
                    Type="forward",
                    TargetGroupArn=Ref(target_group)
                )],
                Conditions=[elb.Condition(
                    Field="path-pattern",
                    Values=['/'],
                )],
            ))
            service_dep = listener_rule.title
        else:
            listener = t.add_resource(elb.Listener(
                "Listener",
                Port=self.vars['ListenerPort'],
                Protocol=protocol,
                LoadBalancerArn=self.vars['LoadBalancerArn'],
                DefaultActions=[elb.Action(
                    Type="forward",
                    TargetGroupArn=Ref(target_group)
                )],
                Certificates=[
                    elb.Certificate(CertificateArn=cert_arn)
                    for cert_arn in self.vars['Certificates']
                ],
            ))
            service_dep = listener.title

        # CloudWatch
        self.log_group = t.add_resource(logs.LogGroup(
            'FargateLogGroup',
            LogGroupName='-'.join(['FargateLogGroup', self.vars['Family']]),
            RetentionInDays=self.vars['LogRetention'],
        ))


        # ECS
        #
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
            ContainerDefinitions=[
                ecs.ContainerDefinition(**self.munge_container_attributes())
            ],
        ))

        service = t.add_resource(ecs.Service(
            'FargateService',
            DependsOn=service_dep,
            Cluster=self.vars['ClusterName'],
            DesiredCount=self.vars['DesiredCount'],
            TaskDefinition=Ref(task_definition),
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
                    TargetGroupArn=Ref(target_group),
                ),
            ],
        ))

        if self.vars['ServiceUrl']:
            self.route53_record_set()
            service_dns = self.vars['ServiceUrl']
        else:
            service_dns = self.vars['LoadBalancerUrl']

        LocalDNS = t.add_output(Output(
            "ServiceDNS",
            Description="The DNS domainname of the service",
            Value=service_dns
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
