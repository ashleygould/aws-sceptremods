===========
Sceptremods
===========

A library of trophosphere modules for use with Sceptre


Installation
____________

Install to python 3.6 virtual environment::

  source ~/python-venv/python3.6/bin/activate
  git clone https://github.com/ashleygould/aws-sceptremods.git
  pip install -d sceptremods


Create a Project
________________

See example project layout in aws-sceptremods/example::

  config/example/config.yaml
                 vpc.yaml
                 vpc-flowlogs.yaml
  hooks/hook_wrappers.py
  resolvers/resolver_wrappers.py
  templates/vpc_wrapper.py
            vpc_flowlogs_wrapper.py


Usage Examples
______________

::

  sceptre  validate-template example vpc
  sceptre  generate-template example vpc
  sceptre launch-env example


Documentation
_____________

https://sceptre.cloudreach.com/latest/about.html
https://github.com/cloudreach/sceptre
https://github.com/cloudreach/sceptre-wordpress-example

