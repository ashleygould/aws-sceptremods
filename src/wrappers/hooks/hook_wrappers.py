"""A collection of wrapper classes for calling custom sceptre hooks from
within sceptre projects.  Each class in this module acts as a pass-though class
to a real custom hook.

This is an unfortunate hack required because sceptre does not currently support
calling hooks via python sys.path.
"""

from sceptremods.hooks.route53 import Route53HostedZone
class Route53HostedZone(Route53HostedZone):
    pass

from sceptremods.hooks.acm_certificate import AcmCertificate
class AcmCertificate(AcmCertificate):
    pass

from sceptremods.hooks.account_verifier import AccountVerifier
class AccountVerifier(AccountVerifier):
    pass

from sceptremods.hooks.ecs_cluster import ECSCluster
class AccountVerifier(ECSCluster):
    pass
 
from sceptremods.hooks.ecs_task_exec_role import ECSTaskExecRole
class AccountVerifier(ECSTaskExecRole):
    pass
