Sceptremods VPC
===============

This project provides EC2 VPC/Subnet resources to be shared by multiple 
ECS Fargate projects.

We are using sceptre V2 syntax

to launch or update templates::
  sceptre --debug --var-file var/common.yaml launch -y common
