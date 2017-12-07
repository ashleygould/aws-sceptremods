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
    #version='0.0.3',
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
    },
)

