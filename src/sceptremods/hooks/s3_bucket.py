# -*- coding: utf-8 -*-
import sys
import boto3

from sceptre.hooks import Hook
from sceptre.cli import setup_logging
from sceptre.exceptions import SceptreException
from sceptre.exceptions import InvalidHookArgumentSyntaxError

DEFAULT_REGION = 'us-west-2'


class S3Bucket(Hook):
    """
    A Sceptre Hook object for managing creation/deletion of S3 buckets.

    self.argument is parsed as a string of keyword args.
    After parsing, the following keywords are accepted:

    :bucket_name:   Required. The name of a s3 bucket.
    :action:        Required. The action to perform on a 3s bucket.
                    Must be one of "create", "empty", or "delete".
    :region:        The AWS region in which to create a bucket.
                    Default: us-west-2.

    Example:
        !s3_bucket action=create bucket_name=mybucket region=us-west-2

    Notes:  The "empty" and "delete" actions recusively remove all objects
            and object versions from a bucket, no questions asked.  Take care!

            If a bucket already exists, the "create" action does nothing.
    """

    def __init__(self, *args, **kwargs):
        super(S3Bucket, self).__init__(*args, **kwargs)

    def run(self):
        kwargs = dict()
        for item in self.argument.split():
            k, v = item.split('=')
            kwargs[k] = v
        required_args = ['action', 'bucket_name']
        for arg in required_args:
            if not arg in kwargs:
                raise InvalidHookArgumentSyntaxError(
                    '{}: required kwarg "{}" not found'.format(__name__, arg)
                )

        s3 = boto3.resource('s3')
        bucket = s3.Bucket(kwargs['bucket_name'])
        action = kwargs['action']
        region = kwargs.get('region', DEFAULT_REGION)

        if action == 'create':
            bucket.load()
            if not bucket.creation_date:
                try:
                    bucket.create(CreateBucketConfiguration={'LocationConstraint': region})
                    self.logger.debug(
                        "{} - Created S3 Bucket: {}".format(__name__, bucket.name)
                    )
                except Exception as e:
                    self.logger.debug(
                        "{} - {}".format(__name__, e)
                    )
            else:
                self.logger.debug(
                    "{} - Found S3 Bucket: {}".format(__name__, bucket.name)
                )

        elif action == 'empty':
            bucket.load()
            self.logger.debug(
                "{} - Deleting contents of S3 Bucket: {}".format(__name__, bucket.name)
            )
            try:
                bucket.objects.delete()
                bucket.object_versions.delete()
            except Exception as e:
                self.logger.debug(
                    "{} - {}".format(__name__, e)
                )

        elif action == 'delete':
            bucket.load()
            self.logger.debug(
                "{} - Deleting S3 Bucket: {}".format(__name__, bucket.name)
            )
            try:
                bucket.objects.delete()
                bucket.object_versions.delete()
                bucket.delete()
            except Exception as e:
                self.logger.debug(
                    "{} - {}".format(__name__, e)
                )

        else:
            raise InvalidHookArgumentSyntaxError(
                '{}: value of kwarg "action" must be one of '
                '"create, empty, delete"'.format(__name__)
            )


def main():
    """
    test s3_bucket hook actions:
        python ./s3_bucket action=create bucket_name=test-bucket.please-delete
    """

    request = S3Bucket(argument=' '.join(sys.argv[1:]))
    request.logger = setup_logging(True, False)
    request.run()


if __name__ == '__main__':
    main()

