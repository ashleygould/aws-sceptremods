
import sys
import time
import re

from sceptre.cli import setup_logging
from sceptre.hooks import Hook
from sceptre.exceptions import SceptreException
from sceptre.exceptions import InvalidHookArgumentSyntaxError
from sceptremods.util import acm


class AcmCertificate(Hook):
    """
    A sceptre hook to generate and validate AWS ACM certificates.
    """

    def __init__(self, *args, **kwargs):
        super(AcmCertificate, self).__init__(*args, **kwargs)


    def handle_cert_request(self, cert_fqdn, validation_domain, region):
        """
        Handle certificate request process.  Allow time for cert to be
        auto-signed.  Times out after 5 minutes.
        """
        acm.request_cert(cert_fqdn, validation_domain, region)
        tries = 0
        max_tries = 30
        interval = 10
        while tries < max_tries:
            time.sleep(interval)
            cert = acm.get_cert_object(cert_fqdn, region)
            if cert['Status'] != 'ISSUED':
                tries += 1
                self.logger.debug('{} - Request status: {}'.format(
                    __name__, cert['Status'])
                )
            else:
                break
        self.logger.debug('{} - Cert: {} - Status: {}'.format(
            __name__, cert_fqdn, cert['Status'])
        )
        return


    def run(self):
        """
        Create a ACM certificate request.  Determine the certificate
        validation method by checking if the validation_domain matches a
        route53 hosted zone in this account.  DNS if yes.  Email if no.
        When validation method is DNS, create validation record set in
        route53.

        self.argument is parsed as a string of keyword args.
        After parsing, the following keywords are accepted:

        :action:            The action to perform.  Must be one of:
                            "request" or "delete".
        :cert_fqdn:         The domain name of the certificate requested.
        :validation_domain: The domain that validates this certificate request.
        :region:            The AWS region in which to create the 
                            certificate.

        Example sceptre config usage:

        hooks:
          before_create:
            - !acm_certificate action=request \
                               cert_fqdn=ashley-demo.example.com \
                               validation_domain=example.com \
                               region=us-east-1
          after_delete:
            - !acm_certificate action=delete \
                               cert_fqdn=ashley-demo.example.com \
                               validation_domain=example.com \
                               region=us-east-1
        """

        # parse self.argument string
        kwargs = dict()
        for item in self.argument.split():
            k, v = item.split('=')
            kwargs[k] = v
        required_args = ['action', 'cert_fqdn', 'validation_domain', 'region']
        missing = []
        for arg in required_args:
            if not arg in kwargs:
                missing.append(arg)
        if missing:
            raise InvalidHookArgumentSyntaxError(
                '{}: required kwargs not found: {}'.format(__name__, missing)
            )
        action = kwargs['action']
        cert_fqdn = kwargs['cert_fqdn']
        validation_domain = kwargs['validation_domain']
        region = kwargs['region']

        # determine certificate status and handle accourdingly
        cert = acm.get_cert_object(cert_fqdn, region)
        if action == 'request':
            if not cert:
                self.logger.debug('{} - Requesting certificate for {}'.format(
                    __name__, cert_fqdn)
                )
                self.handle_cert_request(cert_fqdn, validation_domain, region)

            elif cert['Status'] == 'ISSUED':
                self.logger.debug('{} - Cert: {} - Status: {}'.format(
                    __name__, cert_fqdn, cert['Status'])
                )

            elif cert['Status'] == 'PENDING_VALIDATION':
                self.logger.debug('{} - Cert: {} - Status: {}'.format(
                    __name__, cert_fqdn, cert['Status'])
                )
                if ("ValidationMethod" in cert["DomainValidationOptions"] and 
                    cert["DomainValidationOptions"]["ValidationMethod"] == "DNS"
                ):
                    acm.request_validation(cert, validation_domain, region)

            elif cert['Status'] == 'VALIDATION_TIMED_OUT':
                self.logger.debug('{} - Cert: {} - Status: {}'.format(
                    __name__, cert_fqdn, cert['Status'])
                )
                self.logger.debug('{} - Deleting certificate: {}'.format(
                    __name__, cert['CertificateArn'])
                )
                acm.delete_cert(cert['CertificateArn'], region=region)
                self.logger.debug('{} - Re-requesting certificate: {}'.format(
                    __name__, cert_fqdn)
                )
                self.handle_cert_request(cert_fqdn, validation_domain, region)

            elif cert['Status'] == 'FAILED':
                raise RuntimeError('ACM certificate request failed: {}'.format(
                    cert['FailureReason']))

            elif cert['Status'] == 'REVOKED':
                raise RuntimeError('ACM certificate is in revoked state: {}'.format(
                    cert['RevocationReason']))

            else:
                raise RuntimeError('ACM certificate status is {}'.format(cert['Status']))

        elif action == 'delete':
            if cert:
                self.logger.debug('{} - Deleting certificate: {}'.format(
                    __name__, cert['CertificateArn'])
                )
                acm.delete_cert(cert['CertificateArn'], region=region)

            # clean up route53 certificate validation CNAME entry
            if not cert_fqdn.endswith('.'):
                cert_fqdn += '.'
            validation_cname_pattern=re.compile(r'_\w{32}\.' + re.escape(cert_fqdn))
            record_set = acm.get_resource_record_set(
                hosted_zone=validation_domain,
                record_type='CNAME',
                pattern=validation_cname_pattern,
            )
            if isinstance(record_set, list):
                raise RuntimeError('multiple certificate validation CNAME record sets '
                'found matching "{}"'.format(cert_fqdn)
            )
            if record_set:
                self.logger.debug('{} - Deleting route53 certificate validation '
                    'CNAME: {}'.format(__name__, cert_fqdn)
                )
                acm.change_record_set(record_set, validation_domain, 'DELETE')

        else:
            raise InvalidHookArgumentSyntaxError(
                '{}: value of kwarg "action" must be one of '
                '"request, delete"'.format(__name__)
            )


def main():
    """
    test acm_certificate hook actions:
        python ./acm_certificate.py \
                action=request \
                cert_fqdn=testing00.blee.red \
                validation_domain=blee.red \
                region=us-east-1

    """

    request = AcmCertificate(argument=' '.join(sys.argv[1:]))
    request.logger = setup_logging(True, False)
    request.run()

if __name__ == '__main__':
    main()


