ECS Fargate Resources
=====================

This is a complex example builds out a test and a prod environment stacks to 
deploy a default jboss image in ECS Fargate service.  It also deploys CodeBuild
and CodePipeline resources to automatically update existing ECS tasks from a
custom docker image in ECR.

Dependancies 
------------

EC2 VPC/Subnet resources must be defined in a separate sceptre project.
See ``../vpcinfra``


Launching Environments
----------------------

We are using sceptre V2 syntax

The ``common`` environment contains cfn stacks for ECR repo and EC2 SecurityGroups::
  sceptre --debug --var-file var/common.yaml launch -y common

The ``test`` and ``prod`` evironments contain stacks for ALB, ECS Fargate, 
and CodePipeline::

  sceptre --debug --var-file var/common.yaml --var environment=test launch -y test
  sceptre --debug --var-file var/common.yaml --var environment=prod launch -y prod

Query resources::

  sceptre --var-file var/common.yaml list resources common
  sceptre --var-file var/common.yaml list resources test
  sceptre --var-file var/common.yaml list resources prod

Delete an environment::

  sceptre --debug --var-file var/common.yaml --var environment=test delete -y test
