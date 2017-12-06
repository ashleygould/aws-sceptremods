import pytest
import yaml

import sceptremods
from sceptremods.util.testutil import assert_rendered_template
from sceptremods.templates.vpc import VPC


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

def test_default_vpc(gen_fixture=False):
    t = VPC(dict())
    t.create_template()
    assert_rendered_template(t, 'default_vpc', gen_fixture)

def test_custom_vpc(gen_fixture=False):
    t = VPC(yaml.load(custom_user_data))
    t.create_template()
    assert_rendered_template(t, 'custom_vpc', gen_fixture)

if __name__ == '__main__':
    test_default_vpc(True)
    test_custom_vpc(True)


