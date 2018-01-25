
import sys

from troposphere import (
    GetAtt,
    Join,
    Output,
    Ref,
    ec2,
)

from sceptremods.templates import BaseTemplate


#
# The template class
#
class SG(BaseTemplate):

    VARSPEC = {
        'VpcId': {
            'type': str,
            'description': 'ID of the VPC to use for ecs service.',
            'default': 'bogus-VpcId-for-testing-only',
        },
        'PublicPortMap': {
            'type': list,
            'default': [
                dict(Port='80', Protocol='tcp'),
                dict(Port='443', Protocol='tcp'),
            ],
            'description': 'List of port mappings to allow through public security group',
        },
        'PublicCidr': {
            'type': str,
            'default': '0.0.0.0/0',
            'description': 'The Cidr address from which clients can access the public security group',
        },
    }

    def create_template(self):
        self.vars = self.validate_user_data()
        t = self.template

        public_ingress_rules = list()
        for mapping in self.vars['PublicPortMap']:
            public_ingress_rules.append(ec2.SecurityGroupRule(
                IpProtocol=mapping.get('Protocol', 'tcp'),
                ToPort=mapping['Port'],
                FromPort=mapping['Port'],
                CidrIp=self.vars['PublicCidr'],
            ))
        public_security_group = t.add_resource(ec2.SecurityGroup(
            "PublicSecurityGroup",
            VpcId=self.vars['VpcId'],
            GroupDescription='allow inbound traffic from internet on specified ports',
            SecurityGroupIngress=public_ingress_rules,
        ))

        private_security_group = t.add_resource(ec2.SecurityGroup(
            "PrivateSecurityGroup",
            VpcId=self.vars['VpcId'],
            GroupDescription='allow inbound traffic from public security group on any port',
            SecurityGroupIngress=[ec2.SecurityGroupRule(
                IpProtocol='-1',
                SourceSecurityGroupId=Ref(public_security_group),
            )]
        ))

        t.add_output(Output(
            "PublicSecurityGroup",
            Description="Public Security Group",
            Value=Ref(public_security_group)
        ))
        t.add_output(Output(
            "PrivateSecurityGroup",
            Description="Private Security Group",
            Value=Ref(private_security_group)
        ))


#
# The sceptre handler
#
def sceptre_handler(sceptre_user_data):
    sg = SG(sceptre_user_data)
    sg.create_template()
    return sg.template.to_json()

def main():
    """
    When called as a script, print out the generated template.
    If any arg is supplied, call the template class help method.
    """
    if len(sys.argv) > 1:
        SG().help()
    else:
        print(sceptre_handler(dict()))

if __name__ == '__main__':
    main()

