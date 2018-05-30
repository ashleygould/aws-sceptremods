Docbuilder Website
==================

The docbuilder pattern deploys a documentation website based on Sphinx.  The
website is hosted as a Cloudfront distribution backed by S3 Origin bucket.  We
use sceptre to manage AWS infrastructure.

Prerequisites
-------------

- python > 3.4
- sceptre
- aws-sceptremods

We are using sceptre version 2.  Install sceptre from master branch on github::

    pip install https://github.com/cloudreach/sceptre/archive/master.zip

Install aws-sceptremods from github::

    pip install https://github.com/ashleygould/aws-sceptremods/archive/master.zip

To test building RST docs locally you will also need sphinx::

    pip install sphinx


Configure Sceptre Vars
----------------------

Set site specific sceptre vars in ``sceptre/vars/prod.yaml``.  In this example
we are only hosting a *prod* environment::

    sceptre> vi var/prod.yaml


Launch Docbuilder Infrastructure
--------------------------------

To launch or update AWS infrastructure::

    docbuilder> cd sceptre
    docbuilder/sceptre> sceptre --var-file var/prod.yaml launch -y prod


This launches three cloudformations stacks as configured under ``sceptre/config/prod``:         
- CFS3SitePrereqs: resources required for the Cloudfront Distribution instance.  
  These can potentially be shared by other Cloudfront Distribution instances.
    - Web application firewall (WAF)
    - Cloudfront Origin Access Identity
    - S3 bucket for Cloudfront and S3Origin access logs

- CFS3SiteCFDistribution: Cloudfront Distribution instance, S3 Origin bucket,
  and Route53 record set defining the website.

- CFS3SiteCodePipeline: CodePipeline and CodeBuild instances to build and stage 
  documentation content changes in the Cloudfront Origin bucket.

In addition custom sceptre hooks ensure the existance of the Route53 HostedZone
and the ACM SSL certificate used by the website.


To query the launched stacks::
    sceptre --var-file var/prod.yaml status prod

    sceptre --var-file var/prod.yaml list outputs prod/CFS3SitePrereqs.yaml
    sceptre --var-file var/prod.yaml list outputs prod/CFS3SiteCFDistribution.yaml
    sceptre --var-file var/prod.yaml list outputs prod/CFS3SiteCodePipeline.yaml

    sceptre --var-file var/prod.yaml list resources prod/CFS3SitePrereqs.yaml
    sceptre --var-file var/prod.yaml list resources prod/CFS3SiteCFDistribution.yaml
    sceptre --var-file var/prod.yaml list resources prod/CFS3SiteCodePipeline.yaml

