"""
Wrapper class for route53 custom sceptre hook.  Acts as a pass though class
to the real route53 hook.
"""

from sceptremods.hooks.route53 import Route53HostedZone as WrappedClass

class Route53HostedZone(WrappedClass):
    pass
