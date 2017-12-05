import unittest
import yaml

import sceptremods
from sceptremods.templates.vpc import VPC
from sceptremods.util.testutil import TemplateTestCase


custom_user_data = """
VpcCIDR: 10.128.0.0/16
AZCount: 3
UseDefaultSubnets: False
Tags:
  tag1: value1
  tag2: value2
CustomSubnets:
  Web:
    net_type: public
    priority: 0
  App:
    net_type: private
    gateway_subnet: Web
    priority: 1
  DB:
    net_type: private
    gateway_subnet: Web
    priority: 2
"""


class TestVpcTemplate(TemplateTestCase):

    def test_default_vpc(self):
        vpc = VPC()
        vpc.create_template()
        self.assertRenderedTemplate(vpc, 'default_vpc')

    def test_custom_vpc(self):
        user_data = yaml.load(custom_user_data)
        vpc = VPC(user_data)
        vpc.create_template()
        self.assertRenderedTemplate(vpc, 'custom_vpc')


if __name__ == '__main__':
    unittest.main()



