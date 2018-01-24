"""Wrapper module for sceptremods.templates.alb_log_bucket"""

from sceptremods.templates import alb_log_bucket
def sceptre_handler(sceptre_user_data):
    return alb_log_bucket.sceptre_handler(sceptre_user_data)
