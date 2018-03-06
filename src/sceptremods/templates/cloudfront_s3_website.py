"""
A troposphere module for building static SSL enabled websites as S3 backed
Cloudfront distributions.
"""

import sys

from troposphere import (
    NoValue,
    AccountId,
    GetAtt,
    Join,
    Output,
    Ref,
    s3,
    route53,
)
import troposphere.cloudfront as cf
from troposphere.constants import CLOUDFRONT_HOSTEDZONEID

from sceptremods.templates import BaseTemplate


#
# sceptre_user_data validation functions
#
def validate_run_environment(env):
    allowed_values = ['poc', 'dev', 'qa', 'uat', 'prod']
    if env and env not in allowed_values:
        raise ValueError(
            "'RunEnvironment' must be one of {}.".format(allowed_values)
        )
    return True


#
# The template class
#
class CFS3Site(BaseTemplate):
    """
    Generate cloudformation template to build the following AWS resources:
     - Cloudfront distribution
     - S3 bucket for use as the distribution content origin.
     - Route53 resource record set providing DNS CNAME to the Cloudfront
       distribution.

    The resulting template defines an SSL enabled website.
    """

    VARSPEC = {
        "ApplicationName": {
            "type": str,
            "default": "dummy",
            "description": "Short name of the web application subdomain.",
        },
        "HostedZoneDomainName": {
            "type": str,
            "default": "example.com",
            "description": "The domainname of the AWS Route53 hosted zone to use for the internal DNS CNAME entry.",
        },
        "RunEnvironment": {
            "type": str,
            "default": str(),
            "description": "What service environment this website runs in.  If set, this label gets prepended to the internal DNS name of the website.  Allowed values: 'poc', 'dev', 'qa', 'uat', 'prod'.",
            "validator": validate_run_environment,
        },
        "FQDNInternal": {
            "type": str,
            "default": str(),
            "description": "Website internal FQND.  This is the real DNS domainname for the cloudfront distribution in AWS, but it is not directly reachable.  Only requests to the public domainname (FQDNPublic) will be served.  If nothing is specified, 'FQDNInternal' is automatically set to ${RunEnvironment}.${ApplicationName}.${HostedZoneDomainName}' (e.g. 'poc.dummy.example.com').",
        },
        "FQDNPublic": {
            "type": str,
            "default": str(),
            "description": "Website public FQND.  The SSL cert must match this domainname.  This template does not generate the DNS entry for FQDNPublic.  You must create a DNS CNAME such that FQDNPublic points to the domainname you set in FQDNInternal.",
        },
        "OriginPath": {
            "type": str,
            "default": str(),
            "description": "The path that CloudFront uses to request content from an S3 bucket origin.",
        },
        "DefaultRootObject": {
            "type": str,
            "default": "welcome.html",
            "description": "Default DirectoryIndex page for website.",
        },
        "DefaultTTL": {
            "type": int,
            "default": 0,
            "description": "The default time in seconds that objects stay in CloudFront caches before CloudFront forwards another request to your custom origin to determine whether the object has been updated.",
        },
        "AcmCertificateARN": {
            "type": str,
            "default": str(),
            "description": "AWS ACM certificate arn.  The ACM cert must be defined in AWS region us-east-1.",
        },
        "LogBucket": {
            "type":str, 
            "default": 'cfs3site-log-bucket',
            "description": "S3 logging bucket to record access to s3 origin bucket and cloudfront distribution.",
        },
        "OriginAccessIdentity": {
            "type": str,
            "default": 'DUMMY-ORIGIN-ACCESS-IDENTITY',
            "description": "The CloudFront origin access identity to associate with the origin.",
        },
        "S3CanonicalUserId": {
            "type": str,
            "default": 'DUMMY-S3-CANONICAL-USER-ID',
            "description": "The CloudFront origin access identity S3 canonical user Id.",
        },
        "WebACLId": {
            "type": str,
            "default": str(),
            "description": "The AWS WAF web ACL to associate with this distribution.",
        },
    }


    def origin_bucket(self):
        t = self.template
        self.SiteBucket = t.add_resource(s3.Bucket(
            "SiteBucket",
            DeletionPolicy="Retain",
            VersioningConfiguration=s3.VersioningConfiguration(Status="Enabled"),
            LoggingConfiguration=s3.LoggingConfiguration(
                DestinationBucketName=self.vars["LogBucket"],
                LogFilePrefix=self.vars["FQDNPublic"] + "/bucket_logs/"
            ),
            BucketName="-".join([
                "cfs3site-originbucket",
                self.vars["FQDNInternal"],
            ]),
        ))

        t.add_output(Output(
            "OriginBucket",
            Description="S3 origin bucket for cloudfront distribution",
            Value=Ref(self.SiteBucket),
        ))


    def origin_bucket_policy(self):
        t = self.template
        t.add_resource(s3.BucketPolicy(
            "SiteBucketPolicy",
            Bucket=Ref(self.SiteBucket),
            PolicyDocument={
                "Version": "2012-10-17",
                "Statement": [{
                    "Action": ["s3:GetObject"],
                    "Resource": Join("", ["arn:aws:s3:::", Ref(self.SiteBucket), "/*"]),
                    "Effect": "Allow",
                    "Principal": {
                        "CanonicalUser": self.vars["S3CanonicalUserId"]
                    },
                }],
            },
        ))


    def cloudfront_distribution(self):
        if self.vars["AcmCertificateARN"]:
            viewer_certificate = cf.ViewerCertificate(
                SslSupportMethod="sni-only",
                MinimumProtocolVersion="TLSv1",
                AcmCertificateArn=self.vars["AcmCertificateARN"],
            )
            url_prefix = 'https://'
        else:
            viewer_certificate = NoValue
            url_prefix = 'http://'

        t = self.template
        self.SiteCFDistribution = t.add_resource(cf.Distribution(
            "SiteCFDistribution",
            DistributionConfig=cf.DistributionConfig(
                Comment="S3 Distribution",
                Logging=cf.Logging(
                    Prefix=self.vars["FQDNPublic"] + "/cloudfront_logs/",
                    Bucket=self.vars["LogBucket"] + ".s3.amazonaws.com",
                    IncludeCookies="false"
                ),
                WebACLId=self.vars["WebACLId"],
                Origins=[cf.Origin(
                    S3OriginConfig=cf.S3Origin(
                        OriginAccessIdentity=(
                            "origin-access-identity/cloudfront/"
                            + self.vars["OriginAccessIdentity"]
                        ),
                    ),
                    Id="myS3Origin",
                    DomainName=GetAtt(self.SiteBucket, "DomainName"),
                    OriginPath=self.vars["OriginPath"],
                )],
                DefaultRootObject=self.vars["DefaultRootObject"],
                PriceClass="PriceClass_100",
                Enabled="true",
                DefaultCacheBehavior=cf.DefaultCacheBehavior(
                    ViewerProtocolPolicy="redirect-to-https",
                    ForwardedValues=cf.ForwardedValues(
                        Cookies=cf.Cookies(Forward="none"),
                        QueryString="true"
                    ),
                    TargetOriginId="myS3Origin",
                    DefaultTTL=self.vars["DefaultTTL"],
                ),
                Aliases=[self.vars["FQDNPublic"]],
                ViewerCertificate=viewer_certificate,
            ),
        ))

        CloudFrontDistribution = t.add_output(Output(
            "CloudFrontDistribution",
            Description="Cloudfront distribution domainname in AWS",
            Value=GetAtt(self.SiteCFDistribution, "DomainName"),
        ))
        WebsiteURL = t.add_output(Output(
            "WebsiteURL",
            Description="Public URL of cloudfront hosted website",
            Value=url_prefix + self.vars["FQDNPublic"],
        ))


    def route53_record_set(self):
        t = self.template
        LocalDNS = t.add_resource(route53.RecordSetGroup(
            "LocalDNS",
            HostedZoneName=self.vars["HostedZoneDomainName"] + ".",
            RecordSets=[route53.RecordSet(
                Name=self.vars["FQDNInternal"] + ".",
                Type="A",
                AliasTarget=route53.AliasTarget(
                    HostedZoneId=CLOUDFRONT_HOSTEDZONEID,
                    DNSName=GetAtt(self.SiteCFDistribution, "DomainName"),
                ),
            )],
        ))

        LocalDNS = t.add_output(Output(
            "LocalDNS",
            Description="Internal DNS domainname set in route53",
            Value=self.vars["FQDNInternal"],
        ))


    def create_template(self):
        self.vars = self.validate_user_data()
        if not self.vars["FQDNInternal"]:
            self.vars["FQDNInternal"] = ".".join([
                self.vars["ApplicationName"],
                self.vars["HostedZoneDomainName"],
            ])
            if self.vars["RunEnvironment"]:
                self.vars["FQDNInternal"] = ".".join([
                    self.vars["RunEnvironment"],
                    self.vars["FQDNInternal"],
                ])
        if not self.vars["FQDNPublic"]:
            self.vars["FQDNPublic"] = self.vars["FQDNInternal"]
        if not self.vars["WebACLId"]:
            self.vars["WebACLId"] = NoValue
        if not self.vars["OriginPath"]:
            self.vars["OriginPath"] = NoValue
        else:
            if not self.vars["OriginPath"].startswith('/'):
                self.vars["OriginPath"] = '/' + self.vars["OriginPath"]
            if self.vars["OriginPath"].endswith('/'):
                self.vars["OriginPath"] = self.vars["OriginPath"][:-1]

        self.origin_bucket()
        self.origin_bucket_policy()
        self.cloudfront_distribution()
        self.route53_record_set()

#
# The sceptre handler
#
def sceptre_handler(sceptre_user_data):
    cf_site = CFS3Site(sceptre_user_data)
    cf_site.create_template()
    return cf_site.template.to_json()

def main():
    """
    When called as a script, print out the generated template.
    If any arg is supplied, call the template class help method.
    """
    if len(sys.argv) > 1:
        CFS3Site().help()
    else:
        print(sceptre_handler(dict()))

if __name__ == '__main__':
    main()
