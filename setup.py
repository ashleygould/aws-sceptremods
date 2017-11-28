"""aws-sceptremods setup"""

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='aws-sceptremods',
    version='0.0.2.',
    description='Collection of troposphere template modules for use with spectre',
    long_description=long_description,
    url='https://github.com/ashleygould/aws-sceptremods',
    author='Ashley Gould',
    author_email='agould@ucop.edu',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='aws sceptre troposphere cloudformation',
    packages=find_packages(exclude=['scratch', 'notes']),
    install_requires=['botocore', 'docopt', 'sceptre', 'troposphere'],
)

