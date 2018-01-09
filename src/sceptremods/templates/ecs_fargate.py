import sys
from troposphere import (
    NoValue,
    AccountId,
    GetAtt,
    Join,
    Output,
    Ref,
)
from troposphere import (
    ecs,
    ec2,
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
        'ContainerDefinitions': {
            'type': list,
            'default': [
                dict(
                    Name='nginx',
                    Image='nginx',
                    PortMappings=[dict(ContainerPort=80), dict(ContainerPort=443)],
                    Environment=[dict(Name='BleeKey', Value='Blee')],
                ),
            ],
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


    def create_template(self):
        self.vars = self.validate_user_data()
        t = self.template


        # Security Groups
        #
        alb_security_group = t.add_resource(ec2.SecurityGroup(
            "ALBSecurityGroup",
            VpcId=self.vars['VpcId'],
            GroupDescription='ALB security group to allow inbound traffic from internet',
            SecurityGroupIngress=[
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    ToPort="80",
                    FromPort="80",
                    CidrIp='0.0.0.0/0',
                ),
                #ec2.SecurityGroupRule(
                #    IpProtocol="tcp",
                #    ToPort="443",
                #    FromPort="443",
                #    CidrIp='0.0.0.0/0',
                #),
            ],
        ))

        task_security_group = t.add_resource(ec2.SecurityGroup(
            "TaskSecurityGroup",
            VpcId=self.vars['VpcId'],
            GroupDescription='Task security group to allow inbound traffic ALB security group',
            SecurityGroupIngress=[
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    ToPort="80",
                    FromPort="80",
                    SourceSecurityGroupId=Ref(ALBSecurityGroup),
                ),
                #ec2.SecurityGroupRule(
                #    IpProtocol="tcp",
                #    ToPort="443",
                #    FromPort="443",
                #    SourceSecurityGroupId=Ref(ALBSecurityGroup),
                #),
            ],
        ))



        # ALB
        #
        alb = t.add_resource(elb.LoadBalancer(
            "ApplicationLoadBalancer",
            Name=self.vars['Family'] + '-ALB',
            Type='application',
            Scheme="internet-facing",
            SecurityGroups=[Ref(ALBSecurityGroup)],
            Subnets=[subnet.strip() for subnet in self.vars['PublicSubnets'].split(',')],
        ))
    
        target_group = t.add_resource(elb.TargetGroup(
            "TargetGroup",
            HealthCheckIntervalSeconds="30",
            HealthCheckProtocol="HTTP",
            HealthCheckTimeoutSeconds="10",
            HealthyThresholdCount="4",
            Matcher=elb.Matcher(HttpCode="200"),
            Name=self.vars['Family'] + '-TargetGroup',
            Port="80",
            Protocol="HTTP",
            TargetType='ip',
            UnhealthyThresholdCount="3",
            VpcId=self.vars['VpcId'],
        ))
    
        listener = t.add_resource(elb.Listener(
            "Listener",
            Port="80",
            Protocol="HTTP",
            LoadBalancerArn=Ref(ApplicationLoadBalancer),
            DefaultActions=[elb.Action(
                Type="forward",
                TargetGroupArn=Ref(TargetGroup)
            )],
            #Certificates=[],
        ))

        t.add_output(Output(
            "URL",
            Description="URL of website",
            Value=Join("", ["http://", GetAtt(ApplicationLoadBalancer, "DNSName")])
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
            ExecutionRoleArn=Join('', ['arn:aws:iam::', AccountId, ':role/ecsTaskExecutionRole']),
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
                    SecurityGroups=[Ref(TaskSecurityGroup)],
                )
            ),
            # TODO: pull this info out of Containers var
            LoadBalancers=[
                ecs.LoadBalancer(
                    ContainerName='simplesamlphp',
                    ContainerPort='80',
                    TargetGroupArn=Ref(TargetGroup),
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

