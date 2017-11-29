====================================================================
Sceptremods - a library of trophosphere modules for use with Sceptre


____________
Installation

Install to python 3.6 virtual environment::

  source ~/python-venv/python3.6/bin/activate
  git clone https://github.com/ashleygould/aws-sceptremods.git
  pip install -d sceptremods

________________
Create a Project

See example project layout in aws-sceptremods/example::

  config/example/config.yaml
                 vpc.yaml
                 vpc-flowlogs.yaml
  hooks/hook_wrappers.py
  resolvers/resolver_wrappers.py
  templates/vpc_wrapper.py
            vpc_flowlogs_wrapper.py

______________
Usage Examples

::

  sceptre  validate-template example vpc
  sceptre  generate-template example vpc
  sceptre launch-env example

_____________
Documentation

https://sceptre.cloudreach.com/latest/about.html
https://github.com/cloudreach/sceptre
https://github.com/cloudreach/sceptre-wordpress-example

