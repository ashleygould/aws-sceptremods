"""Generates a cloudformation template to build an RDS instance within an
existing Virtual Private Cloud (VPC)."""

import sys

from troposphere import (
    GetAtt,
    Join,
    Output,
    Ref,
    rds,
    ec2,
)

from sceptremods.templates import BaseTemplate


#
# The template class
#
class RDS(BaseTemplate):
    """RDS sceptremods template class."""

    VARSPEC = {
        # default values are just placeholders when testing troposphere syntax.
        'VpcId': {
            'type': str,
            'default': 'TESTING123',
            'description': 'ID of the VPC to use for ecs service',
        },
        "Subnets": {
            'type': str,
            'default': 'TESTSUBNET1,TESTSUBNET2',
            'description': 'A comma sepatrated list of VPC private subnet IDs to use for this RDS instance',
        },
        "SecurityGroups": {
            'type': list,
            'default': ['TESTDBSG1', 'TESTDBSG2'],
            'description': 'A list of EC2 SecurityGroups in which to place this RDS instance',
        },
        "DBName": {
            'type': str,
            'default': 'MyDatabase',
            'description': 'The database name',
        },
        "DBUser": {
            'type': str,
            'default': 'postgres',
            'description': 'The database admin account username',
        },
        "DBPassword": {
            'type': str,
            'default': 'gobbledigook',
            'description': 'The database admin account password',
        },
        "Engine": {
            'type': str,
            'default': 'postgres',
            'description': 'The database engine that the DB instance uses',
        },
        "EngineVersion": {
            'type': str,
            'default': '9.6.1',
            'description': 'The version number of the database engine that the DB instance uses',
        },
        "DBClass": {
            'type': str,
            'default': 'db.t2.small',
            'description': 'Database instance class',
        },
        "DBAllocatedStorage": {
            'type': int,
            'default': 5,
            'description': 'The size of the database (Gb)',
        },
        "PubliclyAccessible": {
            'type': bool,
            'default': False,
            'description': 'Whether to assign the RDS instance a publicly accessible IP address',
        },
    }

    def create_template(self):
        self.vars = self.validate_user_data()
        t = self.template
        t.add_description(
            "Sceptre stack - create an RDS DBInstance in an existing VPC."
        )

        self.db_subnet_group = t.add_resource(rds.DBSubnetGroup(
            "MyDBSubnetGroup",
            DBSubnetGroupDescription="Subnets available for the RDS DB Instance",
            SubnetIds=[s.strip() for s in self.vars['Subnets'].split(',')],
        ))

        self.db_instance = t.add_resource(rds.DBInstance(
            "DBInstance",
            DBName=self.vars['DBName'],
            AllocatedStorage=self.vars['DBAllocatedStorage'],
            DBInstanceClass=self.vars['DBClass'],
            Engine=self.vars['Engine'],
            EngineVersion=self.vars['EngineVersion'],
            MasterUsername=self.vars['DBUser'],
            MasterUserPassword=self.vars['DBPassword'],
            DBSubnetGroupName=Ref(self.db_subnet_group),
            VPCSecurityGroups=self.vars['SecurityGroups'],
            PubliclyAccessible=self.vars['PubliclyAccessible'],
        ))

        t.add_output(Output(
            "DBEndPoint",
            Description="RDS DB instance endpoint",
            Value=GetAtt(self.db_instance, "Endpoint.Address"),
        ))

        t.add_output(Output(
            "DBPort",
            Description="Network port of the RDS DB instance",
            Value=GetAtt(self.db_instance, "Endpoint.Port"),
        ))


#
# The sceptre handler
#
def sceptre_handler(sceptre_user_data):
    rds = RDS(sceptre_user_data)
    rds.create_template()
    return rds.template.to_json()

def main():
    """
    When called as a script, print out the generated template.
    If any arg is supplied, call the template class help method.
    """
    if len(sys.argv) > 1:
        RDS().help()
    else:
        print(sceptre_handler(dict()))

if __name__ == '__main__':
    main()

