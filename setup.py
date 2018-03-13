#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import io
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with io.open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = '\n' + f.read()

# Load the package's __init__.py module as a dictionary.
about = {}
with open(os.path.join(here, 'src/sceptremods/__init__.py')) as f:
    exec(f.read(), about)

setup(
    name='aws-sceptremods',
    version=about['__version__'],
    description='Collection of troposphere template modules for use with sceptre',
    long_description=long_description,
    url='https://github.com/ashleygould/aws-sceptremods',
    keywords='aws sceptre troposphere cloudformation',
    author='Ashley Gould',
    author_email='agould@ucop.edu',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
    ],
    install_requires=[
        'botocore',
        'boto3',
        'awscli',
        'docopt',
        'PyYAML',
        'sceptre',
        'troposphere',
        'awacs',
    ],
    packages=find_packages(
        'src',
        exclude=[
            'tests',
            'examples',
            'TODO.txt',
            'RELEASE.rst'
        ],
    ),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'sceptremods=sceptremods.cli:main',
        ],
        'sceptre.hooks': [
            'account_verifier = sceptremods.hooks.account_verifier:AccountVerifier',
            'acm_certificate = sceptremods.hooks.acm_certificate:AcmCertificate',
            'ecs_cluster = sceptremods.hooks.ecs_cluster:ECSCluster',
            'ecs_task_exec_role = sceptremods.hooks.ecs_task_exec_role:ECSTaskExecRole',
            'route53_hosted_zone = sceptremods.hooks.route53:Route53HostedZone',
            's3_bucket = sceptremods.hooks.s3_bucket:S3Bucket',
        ],
        'sceptre.resolvers': [
            'certificate_arn = sceptremods.resolvers.certificate_arn:CertificateArn',
            'package_version = sceptremods.resolvers.package_version:PackageVersion',
        ],
    },
)

