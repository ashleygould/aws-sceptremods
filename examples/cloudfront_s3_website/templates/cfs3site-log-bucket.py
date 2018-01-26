from troposphere import (
    Base64,
    Select,
    FindInMap,
    GetAtt,
    GetAZs,
    Join,
    Output,
    If,
    And,
    Not,
    Or,
    Equals,
    Condition,
)
from troposphere import (
    s3,
    Region,
    AccountId,
)
from troposphere import Parameter, Ref, Tags, Template
from troposphere.cloudformation import Init
from troposphere.cloudfront import Distribution, DistributionConfig
from troposphere.cloudfront import Origin, DefaultCacheBehavior
from troposphere.ec2 import PortRange
from troposphere.s3 import BucketPolicy
from troposphere.s3 import Bucket, WebsiteConfiguration


t = Template()

t.add_version("2010-09-09")

t.add_description("""Cloudfront S3 website log bucket""")

CFS3SiteLogBucket = t.add_resource(s3.Bucket(
    "CFS3SiteLogBucket",
    AccessControl="LogDeliveryWrite",
    BucketName=Join(".", ["cfs3site-log-bucket", AccountId]),
))

t.add_resource(s3.BucketPolicy(
    "CFS3SiteLogBucketPolicy",
    Bucket=Ref("CFS3SiteLogBucket"),
    PolicyDocument={
        "Statement": [{
            "Action": ["s3:PutObject"],
            "Principal": { "AWS": [AccountId] },
            "Resource": Join("", ["arn:aws:s3:::", Ref("CFS3SiteLogBucket"), "/*"]),
            "Effect": "Allow",
            "Sid": "CFS3SiteLogBucketPolicy",
        }]
    },
))

t.add_output(Output(
    "CFS3SiteLogBucket",
    Description="Cloudfront S3 website log bucket",
    Value=Ref(CFS3SiteLogBucket),
))

def sceptre_handler(sceptre_user_data):
    return t.to_json()


if __name__ == '__main__':
    print(t.to_json())
