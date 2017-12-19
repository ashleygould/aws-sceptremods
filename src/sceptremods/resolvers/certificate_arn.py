from sceptre.resolvers import Resolver
from sceptremods.util import acm

class CertificateArn(Resolver):

    def __init__(self, *args, **kwargs):
        super(CertificateArn, self).__init__(*args, **kwargs)

    def resolve(self):
        cert_fqdn, region = self.argument.split()
        arn = acm.get_cert_arn(cert_fqdn, region)
        if not arn:
            arn = str()
        self.logger.debug('{} - certificate_arn: {}'.format(__name__, arn))
        return arn


