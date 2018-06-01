# -*- coding: utf-8 -*-
import re
import time
import boto3

DEFAULT_REGION = 'us-east-1'

def get_cert_arn(cert_fqdn, region=DEFAULT_REGION):
    """
    Return the ACM Certificate ARN for 'cert_fqdn'.
    """
    acm_client = boto3.client('acm', region_name=region)
    response = acm_client.list_certificates()
    cert_list = response['CertificateSummaryList']
    while 'NextToken' in response:
        response = acm_client.list_certificates(NextToken=response['NextToken'])
        cert_list += response['CertificateSummaryList']
    arn_list = [
        cert['CertificateArn'] for cert in cert_list
        if cert['DomainName'] == cert_fqdn
    ]
    if len(arn_list) > 1:
        raise RuntimeError(
            "Found multiple matching ACM certificates: {}".format(arn_list)
        )
    if len(arn_list) < 1:
        return None
    return arn_list[0]


def get_cert_object(cert_fqdn, region=DEFAULT_REGION):
    """
    Return the ACM certificate object for 'cert_fqdn'.
    """
    acm_client = boto3.client('acm', region_name=region)
    certificate_arn = get_cert_arn(cert_fqdn, region)
    if certificate_arn:
        return acm_client.describe_certificate(
            CertificateArn=certificate_arn
        )['Certificate']
    else:
        return None


def get_hosted_zone_id(domain_name, region=DEFAULT_REGION):
    """
    Return the hosted zoned Id corresponding to 'domain_name'.
    """
    route53_client = boto3.client('route53', region_name=region)
    response = route53_client.list_hosted_zones()
    hosted_zones = response["HostedZones"]
    while response["IsTruncated"]:
        response = route53_client.list_hosted_zones(
            Marker=reponse["NextMarker"]
        )
        hosted_zones += response["HostedZones"]
    if not domain_name.endswith("."):
        domain_name += "."
    hosted_zone_ids = [
        zone['Id'] for zone in hosted_zones if zone['Name'] == domain_name
    ]
    if len(hosted_zone_ids) > 1:
        raise RuntimeError(
            "Found multiple matching hosted zones: {}".format(cert_list)
        )
    if len(hosted_zone_ids) < 1:
        return None
    return hosted_zone_ids[0].split("/")[2]


def get_elb_hosted_zone_id(elb_arn):
    """
    Return the canonical hosted zoned Id of the given loadbalance arn.
    """
    elb_client = boto3.client('elbv2')
    response = elb_client.describe_load_balancers(LoadBalancerArns=[elb_arn])
    return response['LoadBalancers'][0]['CanonicalHostedZoneId']


def request_cert(cert_fqdn, validation_domain, region=DEFAULT_REGION):
    """
    Create a ACM certificate request.  Determine the certificate
    validation method by checking if the validation_domain matches a
    route53 hosted zone in this account.  DNS if yes.  Email if no.
    When validation method is DNS, create validation record set in
    route53.
    """
    hosted_zone_id = get_hosted_zone_id(validation_domain, region)
    if hosted_zone_id:
        validation_method = 'DNS'
    else:
        validation_method = 'EMAIL'
    acm_client = boto3.client('acm', region_name=region)
    response = acm_client.request_certificate(
        DomainName=cert_fqdn,
        ValidationMethod=validation_method,
        IdempotencyToken='request_cert',
        DomainValidationOptions=[{
            'DomainName': cert_fqdn,
            'ValidationDomain': validation_domain, 
        }]
    )
    arn = response['CertificateArn']
    if validation_method == 'DNS':
        cert = acm_client.describe_certificate(CertificateArn=arn)['Certificate']
        while 'ResourceRecord' not in cert['DomainValidationOptions'][0]:
            time.sleep(5)
            cert = acm_client.describe_certificate(CertificateArn=arn)['Certificate']
        cert_validation_record_set(
            cert['DomainValidationOptions'][0]['ResourceRecord'],
            validation_domain
        )


def delete_cert(cert_arn, region=DEFAULT_REGION):
    """Delete an existing ACM certificate."""
    acm_client = boto3.client('acm', region_name=region)
    response = acm_client.delete_certificate(CertificateArn=cert_arn)
    return


def get_resource_record_set(
        hosted_zone,
        record_type=None,
        pattern=None,
        domain_name=None, 
    ):
    """
    Return route53 resource_record_set by name.

    :domain_name: 
    :hosted_zone: domainname of the route53 hosted zone to query
    """

    # collect all record sets in hosted zone
    client = boto3.client('route53')
    hosted_zone_id = get_hosted_zone_id(hosted_zone)
    response = client.list_resource_record_sets(HostedZoneId=hosted_zone_id)
    records = response['ResourceRecordSets']
    if 'IsTruncated' in response:
        while response['IsTruncated']:
            response = client.list_resource_record_sets(
                HostedZoneId=hosted_zone_id,
                StartRecordName=response['NextRecordName'],
                StartRecordType=response['NextRecordType'],
            )
            records.append(response['ResourceRecordSets'])

    # filter for record set Type
    if record_type:
        records = [r for r in records if r['Type'] == record_type]

    # filter for domain_name or pattern
    if domain_name:
        records = [r for r in records if r['Name'] == domain_name]
    elif pattern:
        records = [r for r in records if pattern.match(r['Name'])]
    else:
        raise ValueError("must supply either 'domain_name' or 'pattern'")
    if len(records) == 0:
        return None
    elif len(records) == 1:
        return records[0]
    return records


def change_record_set(record_set, validation_domain,
        action='UPSERT', comment=str(), region=DEFAULT_REGION):
    """
    Change route53 record.
    """
    valid_actions = ('CREATE', 'DELETE', 'UPSERT')
    if not action in valid_actions:
        raise ValueError('"action" must be one of {}'.format(valid_actions))
    route53_client = boto3.client('route53', region_name=region)
    hosted_zone_id = get_hosted_zone_id(validation_domain, region)
    change_batch ={
        'Comment': comment,
        'Changes': [
            {
                'Action': action,
                'ResourceRecordSet': record_set,
            }
        ]
    }
    response = route53_client.change_resource_record_sets(
        HostedZoneId=hosted_zone_id,
        ChangeBatch=change_batch,
    )


def cert_validation_record_set(resource_record, validation_domain, action='UPSERT'):
    """
    Create/delete route53 record set for ACM certificate validation.
    """
    record_set = {
        'Name': resource_record['Name'],
        'Type': resource_record['Type'],
        'TTL': 300,
        'ResourceRecords': [
            {
                'Value': resource_record['Value'],
            },
        ],
    }
    change_record_set(
        record_set, 
        validation_domain,
        action,
        'acm cert validation',
    )


def request_validation(cert, validation_domain, region=DEFAULT_REGION):
    """
    Resubmit certificate validation request based upon the validation
    options of a certificate (i.e. method is either DNS or EMAIL).
    """
    validation_options = cert['DomainValidationOptions'][0]
    if validation_options['ValidationMethod'] == 'DNS':
        create_validation_record_set(
            validation_options['ResourceRecord'],
            validation_domain,
            region,
        )
    else:
        acm_client = boto3.client('acm', region_name=region)
        acm_client.resend_validation_email(
            CertificateArn=cert['CertificateArn'],
            Domain=cert_fqdn,
            ValidationDomain=validation_domain,
        )
    return
