"""aws-sceptremods setup"""

from os import path
from setuptools import setup, find_packages
#from sceptremods import __version__

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.rst')) as f:
    long_description = f.read()

setup(
    name='aws-sceptremods',
    version='0.0.3',
    #version=__version__,
    description='Collection of troposphere template modules for use with sceptre',
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
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='aws sceptre troposphere cloudformation',
    install_requires=[
        'botocore',
        'docopt',
        'PyYAML',
        'sceptre',
        'troposphere',
        'awacs',
    ],
    packages=find_packages('src', exclude=['tests', 'examples', 'TODO.txt']),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'sceptremods=sceptremods.cli:main',
        ],
    },
    tests_require = [
        'pytest',
    ],
)

