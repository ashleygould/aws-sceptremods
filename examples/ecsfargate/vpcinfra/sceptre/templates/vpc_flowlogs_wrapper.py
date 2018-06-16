"""Wrapper module for sceptremods.templates.vpc_flowlogs"""

from sceptremods.templates import vpc_flowlogs
def sceptre_handler(sceptre_user_data):
    return vpc_flowlogs.sceptre_handler(sceptre_user_data)
