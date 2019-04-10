===========
Sceptremods
===========

A library of trophosphere modules for use with Sceptre


Installation
------------

Install to python 3.6 virtual environment::

  source ~/python-venv/python3.6/bin/activate
  git clone https://github.com/ucopacme/aws-sceptremods.git
  pip install -e aws-sceptremods

 
Query Sceptremods Templates
---------------------------

The sceptremods cli tool lists and prints docs for template modules 
in the library::

  ~> sceptremods --list
  sceptremods modules:
  vpc
  vpc_flowlogs
  
  ~> sceptremods --module vpc
  Sceptremods Version: 0.0.2
  
  Module: vpc
  A troposphere module for generating an AWS cloudformation template
  defining a VPC and subnets.
  
  AWS resources created:
      VPC with attached InternetGateway
      Public and private subnets spanning AvailabilityZones per specification
      NatGatways in Public subnets
      RouteTables and default routes for all subnets.
  [cut]



Sceptremods Config Examples
---------------------------

Under examples/ are sample projects detailing the configuration and usage of
each the primary sceptremods template modules.  Each has a README demonstrating
sceptre command syntax and describing the sample environment.

::

  aws-sceptremods> ls -1 examples/
  basic_vpc
  cloudfront_s3_website
  ecs_fargate




Create a Project
----------------

Run sceptremods cli tool to initialize a new sceptre project::

  sceptremods --init myproject --region us-west-2

This command populates a new project directory with basic sceptre layout and
sceptremods wrappers.  The new project directory and sceptre 'project_code'
take on the name 'sceptre-${PROJECT}'.

::

  ~/tmp> find sceptre-myproject/ -type f
  sceptre-myproject/templates/vpc_wrapper.py
  sceptre-myproject/templates/vpc_flowlogs_wrapper.py
  sceptre-myproject/hooks/hook_wrappers.py
  sceptre-myproject/resolvers/resolver_wrappers.py
  sceptre-myproject/config/config.yaml
  
  ~/tmp> cat sceptre-myproject/config/config.yaml
  project_code: sceptre-myproject
  region: us-west-2

 

Sceptre/Troposphere Documentation
---------------------------------

- https://sceptre.cloudreach.com/latest/about.html
- https://github.com/cloudreach/sceptre
- http://jinja.pocoo.org/docs/2.10/
- https://github.com/cloudtools/troposphere
- https://github.com/cloudtools/awacs


Example Projects
----------------
- https://github.com/cloudreach/sceptre-wordpress-example
- https://github.com/donovan-said/sceptre

