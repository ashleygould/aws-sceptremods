import pytest
import yaml

import sceptremods
from sceptremods.util.testutil import assert_rendered_template
from sceptremods.templates.vpc_flowlogs import FlowLogs


custom_user_data = """
Retention: 5
VpcId: custom-bogus-VpcId-for-testing-only
TrafficType: ACCEPT
Tags:
  tag1: value1
  tag2: value2
"""

def test_default_vpc_flowlogs(gen_fixture=False):
    t = FlowLogs(dict())
    t.create_template()
    assert_rendered_template(t, 'default_vpc_flowlogs', gen_fixture)

def test_custom_vpc_flowlogs(gen_fixture=False):
    t = FlowLogs(yaml.load(custom_user_data))
    t.create_template()
    assert_rendered_template(t, 'custom_vpc_flowlogs', gen_fixture)

if __name__ == '__main__':
    test_default_vpc_flowlogs(True)
    test_custom_vpc_flowlogs(True)
