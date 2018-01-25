# -*- coding: utf-8 -*-
from sceptre.cli import setup_logging
from sceptre.hooks import Hook
from sceptre.exceptions import SceptreException
from sceptre.exceptions import InvalidHookArgumentSyntaxError
from sceptremods.util import acm

DEFAULT_REGION = 'us-east-1'


class AcmCertificate(Hook):
    """
    A sceptre hook to generate and validate AWS ACM certificates.
    """

    def __init__(self, *args, **kwargs):
        super(AcmCertificate, self).__init__(*args, **kwargs)

    def run(self):
        """
        Create a ACM certificate request.  Determine the certificate
        validation method by checking if the validation_domain matches a
        route53 hosted zone in this account.  DNS if yes.  Email if no.
        When validation method is DNS, create validation record set in
        route53.

        self.argument gets split to supply the required positional parameters: 

        :cert_fqdn:         The domain name of the certificate requested.
        :validation_domain: The domain that validates this certificate request.
        :region:            (optional) AWS region in which to create the 
                            certificate.  Default: 'us-east-1'

        Example sceptre config usage:

        hooks:
          before_create:
            - !acm_certificate ashley-demo.example.com example.com us-west-2


        """

        if len(self.argument.split()) == 3:
            cert_fqdn, validation_domain, region = self.argument.split()
        elif len(self.argument.split()) == 2:
            cert_fqdn, validation_domain = self.argument.split()
            region = DEFAULT_REGION
        else:
            raise InvalidHookArgumentSyntaxError(
                '{}: hook requires either two or three positional parameters: '
                'cert_fqdn validation_domain [region]'.format( __name__)
            )

        cert = acm.get_cert_object(cert_fqdn, region)
        if not cert:
            self.logger.debug('{} - Requesting certificate '
                'for {}'.format(__name__, cert_fqdn)
            )
            acm.request_cert(cert_fqdn, validation_domain, region)

        elif cert['Status'] == 'ISSUED':
            self.logger.debug('{} - Certificate issued '
                'for {}'.format(__name__, cert_fqdn)
            )

        elif cert['Status'] == 'PENDING_VALIDATION':
            self.logger.debug('{} - Certificate request is pending validation '
                'for {}'.format(__name__, cert_fqdn)
            )
            #acm.request_validation(cert, validation_domain, region)
"""
  File "/home/agould/git-repos/github/ashleygould/aws-sceptremods/src/sceptremods/hooks/acm_certificate.py", line 70, in run
    acm.request_validation(cert, validation_domain, region)
  File "/home/agould/git-repos/github/ashleygould/aws-sceptremods/src/sceptremods/util/acm.py", line 153, in request_validation
    if validation_options['ValidationMethod'] == 'DNS':
KeyError: 'ValidationMethod'
"""
        elif cert['Status'] == 'VALIDATION_TIMED_OUT':
            self.logger.debug('{} - Certificate request timed out '
                'for {}'.format(__name__, cert_fqdn)
            )
            self.connection_manager.call(
                service="acm",
                command="delete_certificate",
                kwargs=dict(CertificateArn=cert['CertificateArn']),
            )
            self.logger.debug('Re-requesting certificate for {}'.format(cert_fqdn))
            acm.request_cert(cert_fqdn, validation_domain, region)

        elif cert['Status'] == 'FAILED':
            raise RuntimeError('ACM certificate request failed: {}'.format(
                cert['FailureReason']))

        elif cert['Status'] == 'REVOKED':
            raise RuntimeError('ACM certificate is in revoked state: {}'.format(
                cert['RevocationReason']))

        else:
            raise RuntimeError('ACM certificate status is {}'.format(cert['Status']))

def main():
    #cert_fqdn = '*.was.devops.ucop.edu'
    #cert_fqdn = '*.was-poc.devops.ucop.edu'
    #cert_fqdn = 'testing-only-do-not-sign.devops.ucop.edu'
    cert_fqdn = 'testing00.blee.red'
    #validation_domain = 'ucop.edu'
    validation_domain = 'blee.red'
    region = 'us-east-1'
    #region = 'us-west-2'

    param_string = '{} {} {}'.format(cert_fqdn,  validation_domain, region)
    request = AcmCertificate(argument=param_string)
    request.logger = setup_logging(True, False)
    request.run()

if __name__ == '__main__':
    main()


