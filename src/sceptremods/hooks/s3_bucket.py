# -*- coding: utf-8 -*-
import boto3

from sceptre.hooks import Hook
from sceptre.cli import setup_logging


class S3Bucket(Hook):
    """
    Check if the specified s3 bucket exists.  If not, create it.
    """

    def __init__(self, *args, **kwargs):
        super(S3Bucket, self).__init__(*args, **kwargs)

    def run(self):
        bucket_name = self.argument
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(bucket_name)

        bucket.load()
        if not bucket.creation_date:
            response = bucket.create(
                CreateBucketConfiguration={ 'LocationConstraint': 'us-west-2', },
            )
            self.logger.debug("{} - Created S3 Bucket: {}".format(
                __name__, bucket.name)
            )

        else:
            self.logger.debug("{} - Found S3 Bucket: {}".format(
                __name__, bucket.name)
            )

def main():
    "test bucket creation"
    request = S3Bucket(argument='sceptremods-test-bucket.please-delete')
    request.logger = setup_logging(True, False)
    request.run()


if __name__ == '__main__':
    main()

