Sceptremods VPC Example
=======================

the sceptre project path is ``common/vpc.yaml``.  Navigate to the ``sceptre`` directory
to run commands.

::

  > cd sceptre


Commands
--------

show the generated template::

  sceptre> sceptre generate common/vpc.yaml


check if the template is valid::

  sceptre> sceptre validate common/vpc.yaml


check the status of the cfn stack::

  sceptre> sceptre status common/vpc.yaml


list stack outputs::

  sceptre> sceptre list outputs common/vpc.yaml

 
update the stack using a change-set::

  sceptre> sceptre update -c common/vpc.yaml


