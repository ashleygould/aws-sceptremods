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
)
from sceptremods.templates import BaseTemplate


#
# The template class
#
class ECSFargate(BaseTemplate):

    VARSPEC = {
        'Subnets': {
            'type': str,
            'default': str(),
            'description': 'A comma sepatrated list of VPC subnet IDs to use for containers.',
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
        if not self.vars['Subnets']:
            aws_vpc_configuration = NoValue
        else:
            aws_vpc_configuration = ecs.AwsvpcConfiguration(
                AssignPublicIp='ENABLED',
                Subnets=[subnet.strip() for subnet in self.vars['Subnets'].split(',')]
            )
        if not self.vars['Family']:
            self.vars['Family'] = NoValue

        task_definition = t.add_resource(ecs.TaskDefinition(
            'TaskDefinition',
            RequiresCompatibilities=['FARGATE'],
            Family=self.vars['Family'],
            Cpu=str(self.vars['Cpu']),
            Memory=str(self.vars['Memory']),
            NetworkMode='awsvpc',
            ExecutionRoleArn='arn:aws:iam::{}:role/ecsTaskExecutionRole'.format(AccountId),
            ContainerDefinitions=self.munge_container_definitions(),
        ))

        service = t.add_resource(ecs.Service(
            'FargateService',
            Cluster=self.vars['ClusterName'],
            DesiredCount=self.vars['DesiredCount'],
            TaskDefinition=Ref(task_definition),
            LaunchType='FARGATE',
            NetworkConfiguration=ecs.NetworkConfiguration(
                AwsvpcConfiguration=aws_vpc_configuration,
            )
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

