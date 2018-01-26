"""Wrapper module for sceptremods.templates.vpc"""

from sceptremods.templates import cloudfront_s3_website
def sceptre_handler(sceptre_user_data):
    return cloudfront_s3_website.sceptre_handler(sceptre_user_data)
