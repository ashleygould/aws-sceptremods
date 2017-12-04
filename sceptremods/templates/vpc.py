"""
A troposphere module for generating an AWS cloudformation template 
defining a VPC and subnets.

AWS resources created:
    VPC with attached InternetGateway
    Public and private subnets spanning AvailabilityZones per specification
    NatGatways in Public subnets
    RouteTables and default routes for all subnets.

By default we build a Public and a Private subnet in each of 2
AvailabilityZones.  To add custom subnets or span additional AZs, specify
alternative sceptre_user_data values in a vpc.yaml file.  Example:

  sceptre_user_data:
    VpcCIDR: 10.128.0.0/16
    AZCount: 3
    UseDefaultSubnets: False
    Tags:
      tag1: value1
      tag2: value2
    CustomSubnets:
      web:
        net_type: public
        priority: 0
      App:
        net_type: private
        gateway_subnet: Public
        priority: 1
      DB:
        net_type: private
        gateway_subnet: Public
        priority: 2

"""

import sys
import os
from troposphere import (
    Template,
    Ref,
    Output,
    Join,
    Select,
    GetAZs,
    Tags,
    GetAtt,
    ec2
)

from sceptremods.templates import BaseTemplate


#
# Globals
#

# Default public/private subnet layout
DEFAULT_SUBNETS = {
    'Public': dict(
        net_type='public',
        gateway_subnet=None,
        priority=0,
    ),
    'Private': dict(
        net_type='private',
        gateway_subnet='Public',
        priority=1,
    ),
}

# Some global cfn logical resource names
GATEWAY = 'InternetGateway'
GW_ATTACH = 'InternetGatewayAttachment'
VPC_NAME = 'VPC'
VPC_ID = Ref(VPC_NAME)


#
# sceptre_user_data validation functions
#

def validate_cidrblock(cidrblock):
    import re
    cidr_re = re.compile(r'^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$')
    if cidr_re.match(cidrblock):
        ip, mask = cidrblock.split('/')
        for q in ip.split('.'):
            if int(q) > 255:
                raise ValueError("'%s' not a valid cidr block" % cidrblock)
        if int(mask) != 16:
            raise ValueError("'VpcCIDR' must define a class 'B' network")
        return True
    raise ValueError("'%s' not a valid cidr block" % cidrblock)


def validate_az_count(count):
    if count >= 10:
        raise ValueError("Value of 'AZCount' must be an integer less than 10")
    return True


def validate_custom_subnets(custom_subnets):
    for subnet, attributes in custom_subnets.items():
        if not 'net_type' in attributes:
            raise ValueError("User provided subnets must have 'net_type' field")
        if attributes['net_type'] not in ['public', 'private']:
            raise ValueError("Value of 'net_type' field in user provided subnets "
                             "must be one of ['public', 'private']")
        if attributes['net_type'] == 'private':
            if not 'gateway_subnet' in attributes:
                raise ValueError("User provided subnets must have 'gateway_subnet' "
                                 "field if 'net_type' is 'private'")
        if not 'priority' in attributes:
            raise ValueError("User provided subnets must have 'priority' field")
        if not isinstance(attributes['priority'], int) or attributes['priority'] >= 25:
            raise ValueError("Value of 'priority' field in user provided subnets "
                             "must be an integer less than 25")
    return True


#
# The template class
#
class VPC(BaseTemplate):

    VARSPEC = {
        'VpcCIDR': {
            'type': str,
            'default': '10.10.0.0/16',
            'description': (
    """Cidr block for the VPC.  Must define a class B network (i.e. '/16')."""),
            'validator': validate_cidrblock,
        },
        'AZCount': {
            'type': int,
            'default': 2,
            'description': (
    """Number of Availability Zones to use.  Must be an integer less than 10."""),
            'validator': validate_az_count,
        },
        'UseDefaultSubnets': {
            'type': bool,
            'default': True,
            'description': (
    """Whether or not to create the default 'Public' and 'Private' subnets."""),
        },
        'CustomSubnets': {
            'type': dict,
            'default': dict(),
            'description': (
    """Dictionary of custom subnets to create in addition to or instead of the
      default 'Public' and 'Private' subnets.  Each custom subnet is a dictionary
      with the following keys:
        'net_type' - either 'public' or 'private',
        'priority' - integer used to determine the subnet cidr block.  Must
                     be unique among all subnets.
        'gateway_subnet' - the public subnet to use as a default route.
                           Required for subnets of net_type 'private'."""),
            'validator': validate_custom_subnets,
        },
        'Tags': {
            'type': dict,
            'default': dict(),
            'description': (
    """Dictionary of tags to apply to stack resources (e.g. {tagname: value})"""),
        },
    }

    def munge_subnets(self):
        # compose subnet definitions dictionary
        subnets = dict()
        if self.variables['UseDefaultSubnets']:
            subnets.update(DEFAULT_SUBNETS)
        subnets.update(self.variables['CustomSubnets'])
        return subnets


    def availability_zones(self):
        t = self.template
        zones = []
        for i in range(self.variables['AZCount']):
            az = Select(i, GetAZs(''))
            zones.append(az)
        t.add_output(Output('AvailabilityZones', Value=Join(",", zones)))
        return zones


    def subnet_cidr(self, subnets, name, az_index):
        other_priorities = [attr['priority'] for subnet, attr in subnets.items()
                if subnet != name]
        if subnets[name]['priority'] in other_priorities:
            raise ValueError("subnet priority '%d' is not unique for subnet '%s'" %
                    (subnets[name]['priority'], name))
        cidr_parts = self.variables['VpcCIDR'].split('.')
        quod = (subnets[name]['priority'] * 10) + az_index
        cidr_parts[2] = str(quod)
        return '.'.join(cidr_parts).replace('/16','/24')


    def create_vpc(self):
        t = self.template
        t.add_resource(ec2.VPC(
                VPC_NAME,
                CidrBlock=self.variables['VpcCIDR'],
                EnableDnsHostnames=True,
                Tags=Tags(self.variables['Tags']),
                ))
        t.add_output(Output("VpcId", Value=VPC_ID))
        t.add_output(Output("CIDR", Value=self.variables['VpcCIDR']))


    def create_internet_gateway(self):
        t = self.template
        t.add_resource(ec2.InternetGateway(GATEWAY))
        t.add_resource(ec2.VPCGatewayAttachment(
                GW_ATTACH,
                InternetGatewayId=Ref(GATEWAY),
                VpcId=VPC_ID))


    def create_subnets_in_availability_zones(self):
        t = self.template
        subnet_count = 0
        for name in self.subnets.keys():
            self.subnets[name]['az_subnets'] = list()
            for i in range(len(self.zones)):
                subnet_name = '%sSubnet%d' % (name, i)
                self.subnets[name]['az_subnets'].append(subnet_name)
                t.add_resource(ec2.Subnet(
                        subnet_name,
                        AvailabilityZone=self.zones[i],
                        CidrBlock=self.subnet_cidr(self.subnets, name, i),
                        #Tags=Tags(net_type=self.subnets[name]['net_type']) + Tags(self.variables['Tags']),
                        VpcId=VPC_ID))
        # Outputs
        for name in self.subnets:
            t.add_output(Output(
                    '%sSubnets' % name,
                    Value=Join(',', [Ref(sn) for sn in self.subnets[name]['az_subnets']])))


    def create_nat_gateways(self):
        # Nat gateways in public subnets, one per AZ
        t = self.template
        for name in self.subnets.keys():
            if self.subnets[name]['net_type'] == 'public':
                if name == 'Public':
                    prefix = ''
                else:
                    prefix = name
                self.subnets[name]['nat_gateways'] = list()
                for i in range(len(self.zones)):
                    nat_gateway= '%sNatGateway%d' % (prefix, i)
                    nat_gateway_eip = '%sNatGatewayEIP%d' % (prefix, i)
                    self.subnets[name]['nat_gateways'].append(nat_gateway)
                    t.add_resource(ec2.EIP(
                            nat_gateway_eip,
                            Domain='vpc'))
                    t.add_resource(ec2.NatGateway(
                            nat_gateway,
                            SubnetId=Ref(self.subnets[name]['az_subnets'][i]),
                            AllocationId=GetAtt(nat_gateway_eip, 'AllocationId')))


    def create_public_route_tables(self):
        # one route table for each public subnet
        t = self.template
        for name in self.subnets.keys():
            if self.subnets[name]['net_type'] == 'public':
                route_table_name = '%sRouteTable' % name
                self.subnets[name]['route_table'] = route_table_name
                t.add_resource(ec2.RouteTable(
                        #Tags=[ec2.Tag('type', net_type)],
                        route_table_name,
                        VpcId=VPC_ID,))


    def create_private_route_tables(self):
        # one route table for each az for private subnets
        t = self.template
        for name in self.subnets.keys():
            if self.subnets[name]['net_type'] == 'private':
                self.subnets[name]['route_table'] = list()
                for i in range(len(self.zones)):
                    route_table_name = '%sRouteTable%d' % (name, i)
                    self.subnets[name]['route_table'].append(route_table_name)
                    t.add_resource(ec2.RouteTable(
                            #Tags=[ec2.Tag('type', net_type)],
                            route_table_name,
                            VpcId=VPC_ID,))


    def create_route_table_associations(self):
        # Accociate each az subnet to a route table
        t = self.template
        for name in self.subnets.keys():
            for i in range(len(self.zones)):
                if self.subnets[name]['net_type'] == 'public':
                    route_table_name = self.subnets[name]['route_table']
                else:
                    route_table_name = self.subnets[name]['route_table'][i]
                t.add_resource(ec2.SubnetRouteTableAssociation(
                        '%sRouteTableAssociation%d' % (name, i),
                        SubnetId=Ref(self.subnets[name]['az_subnets'][i]),
                        RouteTableId=Ref(route_table_name)))


    def create_default_routes_for_public_subnets(self):
        # Add route through Internet Gateway to route tables for public subnets
        t = self.template
        for name in self.subnets.keys():
            if self.subnets[name]['net_type'] == 'public':
                t.add_resource(ec2.Route(
                        '%sSubnetDefaultRoute' % name,
                        RouteTableId=Ref(self.subnets[name]['route_table']),
                        DestinationCidrBlock='0.0.0.0/0',
                        GatewayId=Ref(GATEWAY)))


    def create_default_routes_for_private_subnets(self):
        # Default routes for private subnets through nat gateways in each az.
        # Use the nat gateways defined in the 'gateway_subnet' for eash subnet.
        t = self.template
        public_subnets = [subnet for subnet, attributes in self.subnets.items()
                if attributes['net_type'] == 'public']
        for name in self.subnets.keys():
            if self.subnets[name]['net_type'] == 'private':
                for i in range(len(self.zones)):
                    gateway_subnet = self.subnets[name]['gateway_subnet']
                    nat_gateway = self.subnets[gateway_subnet]['nat_gateways'][i]
                    if gateway_subnet not in public_subnets:
                        raise ValueError("'%s' is not a valid 'gateway_subnet' name in "
                                "subnet '%s'" % (gateway_subnet, subnet))
                    t.add_resource(ec2.Route(
                            '%sSubnetDefaultRoute%d' % (name, i),
                            RouteTableId=Ref(self.subnets[name]['route_table'][i]),
                            DestinationCidrBlock='0.0.0.0/0',
                            NatGatewayId=Ref(nat_gateway)))


    def create_template(self):
        self.variables = self.validate_user_data()
        self.subnets = self.munge_subnets()
        self.zones = self.availability_zones()
        self.create_vpc()
        self.create_internet_gateway()
        self.create_subnets_in_availability_zones()
        self.create_nat_gateways()
        self.create_public_route_tables()
        self.create_private_route_tables()
        self.create_route_table_associations()
        self.create_default_routes_for_public_subnets()
        self.create_default_routes_for_private_subnets()
        ## debugging
        #print('variables: %s' % self.variables)
        #print('zones: %s' % self.zones)
        #print('subnets: %s' % self.subnets)


#
# The sceptre handler
#
def sceptre_handler(sceptre_user_data):
    vpc = VPC(sceptre_user_data)
    vpc.create_template()
    return vpc.template.to_json()

def main():
    """
    When called as a script, print out the generated template.
    If any arg is supplied, call the template class help method.
    """
    if len(sys.argv) > 1:
        VPC().help()
    else:
        print(sceptre_handler(dict()))

if __name__ == '__main__':
    main()
