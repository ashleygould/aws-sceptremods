"""Wrapper module for sceptremods.templates.ecs_fargate"""

from sceptremods.templates import ecs_fargate
def sceptre_handler(sceptre_user_data):
    return ecs_fargate.sceptre_handler(sceptre_user_data)
