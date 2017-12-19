import pytest
import yaml

from testutil import (
    assert_rendered_template,
    generate_template_fixture,
)


custom_user_data = """
  ApplicationName: ashley-demo
  HostedZoneDomainName: blee.red
  RunEnvironment: poc
  LogBucket: cfs3sitelogbucket
  WebACLId: TrustedSubnetWebACL
  OriginAccessIdentity: CFS3SiteOriginAccessIdentity
  S3CanonicalUserId: CFS3SiteS3CanonicalUserId
  AcmCertificateARN: arn:aws:acm:us-east-1:012345678901:certificate/bogus-acm-identification-string
"""

def test_default_cloudfront_s3_website():
    assert_rendered_template(
            'cloudfront_s3_website',
            'default_cloudfront_s3_website',
            dict())

def test_custom_cloudfront_s3_website():
    assert_rendered_template(
            'cloudfront_s3_website',
            'custom_cloudfront_s3_website',
            yaml.load(custom_user_data))

if __name__ == '__main__':
    generate_template_fixture(
            'cloudfront_s3_website',
            'default_cloudfront_s3_website',
            dict())
    generate_template_fixture(
            'cloudfront_s3_website',
            'custom_cloudfront_s3_website',
            yaml.load(custom_user_data))
