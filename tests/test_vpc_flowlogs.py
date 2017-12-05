import unittest
import yaml

import sceptremods
from sceptremods.util.testutil import TemplateTestCase
from sceptremods.templates.vpc_flowlogs import FlowLogs


custom_user_data = """
Retention: 5
VpcId: custom-bogus-VpcId-for-testing-only
TrafficType: ACCEPT
Tags:
  tag1: value1
  tag2: value2
"""


class TestVpcFlowLogsTemplate(TemplateTestCase):

    def test_default_vpc_flowlogs(self):
        vpc_flowlogs = FlowLogs()
        vpc_flowlogs.create_template()
        self.assertRenderedTemplate(vpc_flowlogs, 'default_vpc_flowlogs')

    def test_custom_vpc(self):
        user_data = yaml.load(custom_user_data)
        vpc_flowlogs = FlowLogs(user_data)
        vpc_flowlogs.create_template()
        self.assertRenderedTemplate(vpc_flowlogs, 'custom_vpc_flowlogs')


if __name__ == '__main__':
    unittest.main()



