"""A collection of wrapper classes for calling custom sceptre resolvers from
within sceptre projects.  Each class in this module acts as a pass-though class
to a real custom resolver.

This is an unfortunate hack required because sceptre does not currently support
calling resolvers via python sys.path.
"""

from sceptremods.resolvers.package_version import PackageVersion
class PackageVersion(PackageVersion):
    """Wrapper class for sceptremods.resolvers.package_version.PackageVersion"""
    pass

from sceptremods.resolvers.certificate_arn import CertificateArn
class CertificateArn(CertificateArn):
    """Wrapper class for sceptremods.resolvers.certificate_arn.CertificateArn"""
    pass
