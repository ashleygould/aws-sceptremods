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
