
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
class ALB(BaseTemplate):

    VARSPEC = {
        'VpcId': {
            'type': str,
            'description': 'ID of the VPC to use for ecs service.',
            'default': 'bogus-VpcId-for-testing-only',
        },
        'PublicSubnets': {
            'type': str,
            'default': str(),
            'description': 'A comma sepatrated list of VPC public subnet IDs to use for ELB.',
            #'validator': comma_separated_values,
        },
        'PublicCidr': {
            'type': str,
            'default': '0.0.0.0/0',
            'description': 'The Cidr address from which clients can access the ALB',
        },
        'PublicSecurityGroup': {
            'type': str,
            'default': str(),
            'description': 'Security group in which to place the ALB',
        },
        'LogBucket': {
            'type': str,
            'default': str(),
            'description': 'Name of an S3 bucket where access log files are stored',
        },
        'LogPrefix': {
            'type': str,
            'default': str(),
            'description': 'A prefix for the all log object keys',
        },
    }

    def create_template(self):
        self.vars = self.validate_user_data()
        t = self.template

        if self.vars['LogBucket']:
            elb_attrubutes = [
                elb.LoadBalancerAttributes(Key='access_logs.s3.enabled', Value='true'),
                elb.LoadBalancerAttributes(Key='access_logs.s3.bucket', Value=self.vars['LogBucket']),
                elb.LoadBalancerAttributes(Key='access_logs.s3.prefix', Value=self.vars['LogPrefix']),
            ]
        else:
            elb_attrubutes = NoValue

        alb = t.add_resource(elb.LoadBalancer(
            "ApplicationLoadBalancer",
            Type='application',
            Scheme="internet-facing",
            SecurityGroups=[self.vars['PublicSecurityGroup']],
            Subnets=[subnet.strip() for subnet in self.vars['PublicSubnets'].split(',')],
            LoadBalancerAttributes=elb_attrubutes,
        ))
    
        default_target_group = t.add_resource(elb.TargetGroup(
            "TargetGroup",
            Port='80',
            Protocol='HTTP',
            VpcId=self.vars['VpcId'],
        ))
    
        default_listener = t.add_resource(elb.Listener(
            "DefaultListener",
            Port='80',
            Protocol='HTTP',
            LoadBalancerArn=Ref(alb),
            DefaultActions=[elb.Action(
                Type="forward",
                TargetGroupArn=Ref(default_target_group)
            )],
        ))

        t.add_output(Output(
            "LoadBalancerArn",
            Description="A reference to the Application Load Balancer",
            Value=Ref(alb),
        ))

        t.add_output(Output(
            "LoadBalancerUrl",
            Description="URL of the ALB",
            Value=GetAtt(alb, "DNSName"),
        ))

        t.add_output(Output(
            "DefaultListener",
            Description="A reference to a port 80 listener",
            Value=Ref(default_listener),
        ))


#
# The sceptre handler
#
def sceptre_handler(sceptre_user_data):
    alb = ALB(sceptre_user_data)
    alb.create_template()
    return alb.template.to_json()

def main():
    """
    When called as a script, print out the generated template.
    If any arg is supplied, call the template class help method.
    """
    if len(sys.argv) > 1:
        ALB().help()
    else:
        print(sceptre_handler(dict()))

if __name__ == '__main__':
    main()

