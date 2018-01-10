"""
Assumptions:
    using fargate
    using ALB
    only one publicly available container
    only one port on publicly available container
    ALB in public subnets
    ecs service in private subnets
"""

import sys
import itertools

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
    ec2,
    logs,
)
import troposphere.elasticloadbalancingv2 as elb

from sceptremods.templates import BaseTemplate


#
# The template class
#
class ECSFargate(BaseTemplate):

    VARSPEC = {
        'VpcId': {
            'type': str,
            'description': 'ID of the VPC to use for ecs service.',
            #'default': 'bogus-VpcId-for-testing-only',
        },
        'PublicSubnets': {
            'type': str,
            'default': str(),
            'description': 'A comma sepatrated list of VPC public subnet IDs to use for ELB.',
            #'validator': comma_separated_values,
        },
        'PrivateSubnets': {
            'type': str,
            'default': str(),
            'description': 'A comma sepatrated list of VPC private subnet IDs to use for containers.',
            #'validator': comma_separated_values,
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
        'Cpu': {
            'type': int,
            'default': 256,
            'description': 'The number of cpu units used by the task.  Must be one of [256, 512, 1024, 2048, 4096].',
        },
        'Memory': {
            'type': int,
            'default': 512,
            'description': 'The amount (in MiB) of memory used by the task.  Must be on of??',
        },
        'Family': {
            'type': str,
            'default': str(),
            'description': 'The name of a family that this task definition is registered to. ',
        },
        'LogRetention': {
            'type': int,
            'default': 14,
            'description': 'Number of days to retain cloudwatch logs',
        },
        'Certificates': {
            'type': list,
            'default': list(),
            'description': 'A list of ssl certs',
        },
        'PublicCidr': {
            'type': str,
            'default': '0.0.0.0/0',
            'description': 'The Cidr address from which clients can access the ALB',
        },
        'PublicContainer': {
            'type': str,
            'default': str(),
            'description': "Name of the container accessible through the ALB.  This name maps to a 'Name' attribute in the 'ContainerDefinitions' variable.  If not are specified, then we use the first item in 'ContainerDefinitions'.",
        },
        'ContainerDefinitions': {
            'type': list,
            'default': [dict(
                Name='nginx',
                Image='nginx',
                PortMappings=[dict(
                    ContainerPort=8080,
                    HostPort=80,
                    Protocol='tcp'
                )],
            )],
            'description': (
  """List of container definitions each of which is a dictionary with the
  following keys:

    {
      "Command" : [ String, ... ],
      "Cpu" : Integer,
      "DisableNetworking" : Boolean,
      "DnsSearchDomains" : [ String, ... ],
      "DnsServers" : [ String, ... ],
      "DockerLabels" : { String:String, ... },
      "DockerSecurityOptions" : [ String, ... ],
      "EntryPoint" : [ String, ... ],
      "Environment" : [ KeyValuePair, ... ],
      "Essential" : Boolean,
      "ExtraHosts" : [ HostEntry, ... ],
      "Hostname" : String,
      "Image" : String,
      "Links" : [ String, ... ],
      "LinuxParameters" : LinuxParameters,
      "LogConfiguration" : LogConfiguration,
      "Memory" : Integer,
      "MemoryReservation" : Integer,
      "MountPoints" : [ MountPoint, ... ],
      "Name" : String,
      "PortMappings" : [ PortMapping, ... ],
      "Privileged" : Boolean,
      "ReadonlyRootFilesystem" : Boolean,
      "Ulimits" : [ Ulimit, ... ],
      "User" : String,
      "VolumesFrom" : [ VolumeFrom, ... ],
      "WorkingDirectory" : String
    }
    """),
        },
    }

    def munge_container_definitions(self):
        container_definitions = list()
        for d in self.vars['ContainerDefinitions']:

            if 'Environment' in d:
                d['Environment'] = [ecs.Environment(**m) for m in d['Environment']]
            if 'ExtraHosts' in d:
                d['ExtraHosts'] = [ecs.HostEntry(**m) for m in d['ExtraHosts']]
            #if 'LinuxParameters' in d:
            #    d['LinuxParameters'] = [ecs.LinuxParameters(**m) for m in d['LinuxParameters']]
            if 'LogConfiguration' in d:
                d['LogConfiguration'] = [ecs.LogConfiguration(**m) for m in d['LogConfiguration']]
            else:
                d['LogConfiguration'] =  ecs.LogConfiguration(
                    LogDriver='awslogs',
                    Options={
                        'awslogs-group': Ref(self.log_group),
                        'awslogs-region': Region,
                        'awslogs-stream-prefix': d['Name'],
                    },
                )
            if 'MountPoints' in d:
                d['MountPoints'] = [ecs.MountPoint(**m) for m in d['MountPoints']]
            if 'PortMappings' in d:
                d['PortMappings'] = [ecs.PortMapping(**m) for m in d['PortMappings']]
            if 'Ulimit' in d:
                d['Ulimit'] = [ecs.Ulimit(**m) for m in d['Ulimit']]
            #if 'VolumesFrom' in d:
            #    d['VolumesFrom'] = [ecs.VolumesFrom(**m) for m in d['VolumesFrom']]

            container_definitions.append(ecs.ContainerDefinition(**d))
        return container_definitions


    def public_port_map(self):
        if not self.vars['PublicContainer']:
            self.vars['PublicContainer'] = self.vars['ContainerDefinitions'][0]['Name']
        public_port_mappings = [
            d['PortMappings'] for d in self.vars['ContainerDefinitions']
            if d['Name'] == self.vars['PublicContainer']
        ]
        # flatten list of port mappings
        public_port_mappings = list(itertools.chain.from_iterable(public_port_mappings))
        #print(public_port_mappings)
        return public_port_mappings


    def create_template(self):
        self.vars = self.validate_user_data()
        t = self.template
        public_port_mappings = self.public_port_map()

        # Security Groups
        #
        alb_ingress_rules = list()
        for mapping in public_port_mappings:
            #print(mapping)
            alb_ingress_rules.append(ec2.SecurityGroupRule(
                IpProtocol=mapping.get('Protocol', 'tcp'),
                ToPort=mapping['ContainerPort'],
                FromPort=mapping['ContainerPort'],
                CidrIp=self.vars['PublicCidr'],
            ))
        alb_security_group = t.add_resource(ec2.SecurityGroup(
            "ALBSecurityGroup",
            VpcId=self.vars['VpcId'],
            GroupDescription='allow inbound traffic from internet',
            SecurityGroupIngress=alb_ingress_rules,
        ))

        task_ingress_rules = list()
        for mapping in public_port_mappings:
            task_ingress_rules.append(ec2.SecurityGroupRule(
                IpProtocol=mapping.get('Protocol', 'tcp'),
                ToPort=mapping['ContainerPort'],
                FromPort=mapping['ContainerPort'],
                SourceSecurityGroupId=Ref(alb_security_group),
            ))
        task_security_group = t.add_resource(ec2.SecurityGroup(
            "TaskSecurityGroup",
            VpcId=self.vars['VpcId'],
            GroupDescription='allow inbound traffic from ALB security group',
            SecurityGroupIngress=task_ingress_rules,
        ))


        # ALB
        #
        # Using the first port mapping for default listener config
        public_port = public_port_mappings[0]['ContainerPort'] 
        if self.vars['Certificates']:
            protocol = 'HTTPS'
        else:
            protocol = 'HTTP'

        alb = t.add_resource(elb.LoadBalancer(
            "ApplicationLoadBalancer",
            Name=self.vars['Family'] + '-ALB',
            Type='application',
            Scheme="internet-facing",
            SecurityGroups=[Ref(alb_security_group)],
            Subnets=[subnet.strip() for subnet in self.vars['PublicSubnets'].split(',')],
        ))
    
        target_group = t.add_resource(elb.TargetGroup(
            "TargetGroup",
            HealthCheckIntervalSeconds="30",
            HealthCheckProtocol=protocol,
            HealthCheckTimeoutSeconds="10",
            HealthyThresholdCount="4",
            Matcher=elb.Matcher(HttpCode="200"),
            Name=self.vars['Family'] + '-TargetGroup',
            Port=public_port,
            Protocol=protocol,
            TargetType='ip',
            UnhealthyThresholdCount="3",
            VpcId=self.vars['VpcId'],
        ))
    
        listener = t.add_resource(elb.Listener(
            "Listener",
            Port=public_port,
            Protocol=protocol,
            LoadBalancerArn=Ref(alb),
            DefaultActions=[elb.Action(
                Type="forward",
                TargetGroupArn=Ref(target_group)
            )],
            #Certificates=[],
        ))

        t.add_output(Output(
            "URL",
            Description="URL of website",
            Value=Join("", ["http://", GetAtt(alb, "DNSName")])
        ))

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
            ContainerDefinitions=self.munge_container_definitions(),
        ))

        service = t.add_resource(ecs.Service(
            'FargateService',
            DependsOn=['Listener'],
            Cluster=self.vars['ClusterName'],
            DesiredCount=self.vars['DesiredCount'],
            TaskDefinition=Ref(task_definition),
            LaunchType='FARGATE',
            NetworkConfiguration=ecs.NetworkConfiguration(
                AwsvpcConfiguration=ecs.AwsvpcConfiguration(
                    Subnets=[s.strip() for s in self.vars['PrivateSubnets'].split(',')],
                    SecurityGroups=[Ref(task_security_group)],
                )
            ),
            LoadBalancers=[
                ecs.LoadBalancer(
                    ContainerName=self.vars['PublicContainer'],
                    ContainerPort=public_port,
                    TargetGroupArn=Ref(target_group),
                ),
            ],
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




#  CloudwatchLogsGroup:
#    Type: AWS::Logs::LogGroup
#    Properties:
#      LogGroupName: !Join ['-', [ECSLogGroup, !Ref 'AWS::StackName']]
#      RetentionInDays: 14
#---
#  taskdefinition:
#    Type: AWS::ECS::TaskDefinition
#    Properties:
#      ContainerDefinitions:
#        LogConfiguration:
#          LogDriver: awslogs
#          Options:
#            awslogs-group:
#              Ref: CloudwatchLogsGroup
#            awslogs-region: !Ref 'AWS::Region'
#            awslogs-stream-prefix: ecs-demo-app

