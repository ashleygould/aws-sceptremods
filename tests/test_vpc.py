import pytest
import yaml

from testutil import (
    assert_rendered_template,
    generate_template_fixture,
)

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

def test_default_vpc():
    assert_rendered_template('vpc', 'default_vpc', dict())

def test_custom_vpc():
    assert_rendered_template('vpc', 'custom_vpc', yaml.load(custom_user_data))

if __name__ == '__main__':
    generate_template_fixture('vpc', 'default_vpc', dict())
    generate_template_fixture('vpc', 'custom_vpc', yaml.load(custom_user_data))


