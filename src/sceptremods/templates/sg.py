"""
Assumptions:
    security groups reside in a VPC
    only ipv4 ip and cidr addresses
    no egress rules, only ingress rules
"""


import sys

from troposphere import (
    AccountId,
    GetAtt,
    Join,
    NoValue,
    Output,
    Region,
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
            'description': 'ID of the VPC where to define security groups',
            'default': 'BOGUS-VPCID-FOR-TESTING-ONLY',
        },
        'SecurityGroups': {
            'type': list,
            'description': 'List of dictionaries of EC2 SecurityGroup parameters',
            'default': [
                dict(
                    name='PublicSG',
                    description='allow inbound traffic from internet on specified ports',
                    ingress_rules=[
                        dict(port='80', proto='tcp', source_ip='0.0.0.0/0'),
                        dict(port='443', proto='tcp', source_ip='0.0.0.0/0'),
                    ],
                ),
                dict(
                    name="PrivateSG",
                    description='allow inbound traffic from public security group on any port',
                    ingress_rules=[
                        dict(source_sg='PublicSG'),
                    ],
                ),
            ],
        },
    }

    def create_template(self):
        self.vars = self.validate_user_data()
        t = self.template

        self.security_groups = dict()
        for sg_params in self.vars['SecurityGroups']:
            if 'ingress_rules' in sg_params:
                ingress_rules = list()

                # munge ingress rule attributes
                r_attr = dict()
                for rule in sg_params['ingress_rules']:

                    if 'source_sg' in rule and rule['source_sg']:
                        r_attr['SourceSecurityGroupId'] = Ref(rule['source_sg'])

                    if 'source_ip' in rule and rule['source_ip']:
                        r_attr['CidrIp'] = rule['source_ip']

                    if 'port' in rule and rule['port']:
                        if str(rule['port']).rfind('-') != -1:
                            r_attr['ToPort'], r_attr['FromPort'] = str(rule['port']).split('-')
                        else:
                            r_attr['ToPort'] = str(rule['port'])
                            r_attr['FromPort'] = str(rule['port'])

                    if not 'proto' in rule:
                        r_attr['IpProtocol'] = '-1'
                    else:
                        r_attr['IpProtocol'] = rule['proto']

                    ingress_rules.append(ec2.SecurityGroupRule(**r_attr))

            self.security_groups[sg_params['name']] = t.add_resource(ec2.SecurityGroup(
                sg_params['name'],
                VpcId=self.vars['VpcId'],
                GroupDescription=sg_params['description'],
                SecurityGroupIngress=ingress_rules,
            ))

            t.add_output(Output(
                sg_params['name'],
                Description=sg_params['description'],
                Value=Ref(self.security_groups[sg_params['name']])
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

