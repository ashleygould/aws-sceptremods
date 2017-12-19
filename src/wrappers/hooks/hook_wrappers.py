"""A collection of wrapper classes for calling custom sceptre hooks from
within sceptre projects.  Each class in this module acts as a pass-though class
to a real custom hook.

This is an unfortunate hack required because sceptre does not currently support
calling hooks via python sys.path.
"""

from sceptremods.hooks.route53 import Route53HostedZone
class Route53HostedZone(Route53HostedZone):
    """Wrapper class for sceptremods.hooks.route53.Route53HostedZone"""
    pass

from sceptremods.hooks.acm_certificate import AcmCertificate
class AcmCertificate(AcmCertificate):
    """Wrapper class for sceptremods.hooks.acm_certificate.AcmCertificate"""
    pass

from sceptremods.hooks.account_verifier import AccountVerifier
class AccountVerifier(AccountVerifier):
    """Wrapper class for sceptremods.hooks.account_verifier.AccountVerifier"""
    pass
