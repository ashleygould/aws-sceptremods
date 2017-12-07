import pytest
import yaml

from testutil import (
    assert_rendered_template,
    generate_template_fixture,
)


custom_user_data = """
Retention: 5
VpcId: custom-bogus-VpcId-for-testing-only
TrafficType: ACCEPT
Tags:
  tag1: value1
  tag2: value2
"""

def test_default_vpc_flowlogs():
    assert_rendered_template('vpc_flowlogs', 'default_vpc_flowlogs', dict())

def test_custom_vpc_flowlogs():
    assert_rendered_template(
            'vpc_flowlogs', 'custom_vpc_flowlogs', yaml.load(custom_user_data))

if __name__ == '__main__':
    generate_template_fixture('vpc_flowlogs', 'default_vpc_flowlogs', dict())
    generate_template_fixture(
            'vpc_flowlogs', 'custom_vpc_flowlogs', yaml.load(custom_user_data))
