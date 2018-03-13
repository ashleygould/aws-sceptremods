"""A collection of wrapper classes for calling custom sceptre hooks from
within sceptre projects.  Each class in this module acts as a pass-though class
to a real custom hook.

This is an unfortunate hack required because sceptre does not currently support
calling hooks via python sys.path.  Sceptre v2 resolves this issue.  See:
https://github.com/cloudreach/sceptre/wiki/Roadmap
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
class ECSCluster(ECSCluster):
    pass
 
from sceptremods.hooks.ecs_task_exec_role import ECSTaskExecRole
class ECSTaskExecRole(ECSTaskExecRole):
    pass
 
from sceptremods.hooks.s3_bucket import S3Bucket
class S3Bucket(S3Bucket):
    pass

from sceptremods.hooks.experimental.zappa_lambda import ZappaLambda
class ZappaLambda(ZappaLambda):
    pass
