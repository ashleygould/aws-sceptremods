Release 0.0.5 - Tue Dec 19 14:21:36 PST 2017
 - add template.cloudfront_s3_website; add util.acm
 - sceptremods.template.VarSpec: format descriptions using textwrap
 - validate python 2.7 support
 - travis working for python 3.6. added 2.7
 - debuging travis config

Release 0.0.4 - Thu Dec  7 12:09:14 PST 2017
 - tweek setup.py,  add .travis.yml
 - reorganize project dir.  move packages under src/
 - rework testutils and template tests
 - convert all tests to pytest instead of unittest
 - add tests for vpc_flowlogs.py
 - add testing code: so far only tests vpc.py template.

Release 0.0.3 - Mon Dec  4 14:20:31 PST 2017
 - complete sceptremods.cli
 - add scripts.sceptrmods
 - update README

Release 0.0.2 - Mon Nov 27 16:50:50 PST 2017
 - add template wrapper: vpc_flowlogs_wrapper.py
 - add new template mod: vpc_flowlogs
 - convert vpc.py into scpectermods.template.BaseTemplate
 - sceptremods.templates: create classes: VarSpec, BaseTemplate
 - complete testing on custom hooks/resolvers
 - add resolver package_version.py
 - make wrapper class for route53 hook
 - hooks/route53.py: hook route53_hosted_zone tested. working.
 - developing route53 hook from stacker example

Release 0.0.1 - Wed Nov 22 16:21:41 2017 -0800
 - reorg config and sceptremods
 - prep package release: add setup.py
 - add templates/vpc_wrapper.py
 - vpc.py: rework variable validation
 - initial commit

