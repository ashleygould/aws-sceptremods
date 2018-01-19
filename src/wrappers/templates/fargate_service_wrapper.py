"""Wrapper module for sceptremods.templates.fargate_service"""

from sceptremods.templates import fargate_service
def sceptre_handler(sceptre_user_data):
    return fargate_service.sceptre_handler(sceptre_user_data)
