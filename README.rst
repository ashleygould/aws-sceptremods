===========
Sceptremods
===========

A library of trophosphere modules for use with Sceptre


Installation
------------

Install to python 3.6 virtual environment::

  source ~/python-venv/python3.6/bin/activate
  git clone https://github.com/ashleygould/aws-sceptremods.git
  pip install -d sceptremods


Create a Project
----------------

See example project layout in aws-sceptremods/example::

  config/example/config.yaml
                 vpc.yaml
                 vpc-flowlogs.yaml
  hooks/hook_wrappers.py
  resolvers/resolver_wrappers.py
  templates/vpc_wrapper.py
            vpc_flowlogs_wrapper.py


Usage Examples
--------------

::

  sceptre  validate-template example vpc
  sceptre  generate-template example vpc
  sceptre launch-env example


Documentation
-------------

- https://sceptre.cloudreach.com/latest/about.html
- https://github.com/cloudreach/sceptre
- http://jinja.pocoo.org/docs/2.10/
- https://github.com/cloudtools/troposphere
- https://github.com/cloudtools/awacs


Example projects
----------------
- https://github.com/cloudreach/sceptre-wordpress-example
- https://github.com/donovan-said/sceptre

