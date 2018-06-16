Fargate Project Reference Architecture
======================================

This is a complex example builds out a dev, qa and a prod environment stacks to 
deploy a default Apache-PHP image in ECS Fargate service.  It also deploys CodeBuild
and CodePipeline resources to automatically update existing ECS tasks from a
custom docker image in ECR.  

The project source git repository lives under bitbucket.  See:
``git@bitbucket.org:UWAS/ecsfargate-refarch.git``

Dependancies 
------------

EC2 VPC/Subnet/SecurityGroups resources must be defined in a separate sceptre project.
See: ``git@bitbucket.org:UWAS/ecsfargate-refarch.git/vpcinfra``

Bitbucket source repository and AWS authentication tokens.  
See ``./bitbucket_and_codepipeline.txt``


Stack Names
-----------

Infrastructure stacks::

  sceptre-vpcinfra-dev-vpc
  sceptre-vpcinfra-dev-vpcflowlogs
  sceptre-vpcinfra-dev-sg
  
  sceptre-vpcinfra-qa-vpc
  sceptre-vpcinfra-qa-vpcflowlogs
  sceptre-vpcinfra-qa-sg
  
  sceptre-vpcinfra-prod-vpc
  sceptre-vpcinfra-prod-vpcflowlogs
  sceptre-vpcinfra-prod-sg

Application stacks::

  sceptre-ecsrefarch-common-ecr
  sceptre-ecsrefarch-common-bitbucketsync
  
  sceptre-ecsrefarch-dev-alb
  sceptre-ecsrefarch-dev-ecsfargate
  sceptre-ecsrefarch-dev-pipeline
  
  sceptre-ecsrefarch-qa-alb
  sceptre-ecsrefarch-qa-ecsfargate
  sceptre-ecsrefarch-qa-pipeline
  
  sceptre-ecsrefarch-prod-alb
  sceptre-ecsrefarch-prod-ecsfargate
  sceptre-ecsrefarch-prod-pipeline



Sceptre and Sceptremods
-----------------------

Sceptre and sceptremods installation into python 3 venv::

  . ~/python-venv/python3.6/bin/activate
  pip install https://github.com/cloudreach/sceptre/archive/master.zip
  pip install https://github.com/ashleygould/aws-sceptremods/archive/master.zip


Sceptre syntax help::

  sceptre --help
  sceptre launch --help


Building Infrastructure Stacks
------------------------------

Run sceptre commands from the *vpcinfra/sceptre* directory.

Launch/update all stacks in *dev* environment::

  cd vpcinfra/sceptre
  sceptre \
  --var-file var/common.yaml \
  --var-file var/dev.yaml \
  launch --yes dev

Query all stack outputs::

  sceptre \
  --var-file var/common.yaml \
  --var-file var/dev.yaml \
  list outputs dev


Building Application Stacks
---------------------------

Run sceptre commands from the *devops/sceptre* directory.

Launch/update all stacks in *dev* environment::

  cd devops/sceptre
  sceptre \
  --var-file var/common.yaml \
  --var-file var/dev.yaml \
  launch --yes dev

Manage just the ecsfargate stack in *dev*::  

  sceptre \
  --debug \
  --var-file var/common.yaml \
  --var-file var/dev.yaml \
  create --yes \
  dev/ecsfargate.yaml

  sceptre \
  --debug \
  --var-file var/common.yaml \
  --var-file var/dev.yaml \
  update --yes \
  dev/ecsfargate.yaml

  sceptre \
  --debug \
  --var-file var/common.yaml \
  --var-file var/dev.yaml \
  delete --yes \
  dev/ecsfargate.yaml

