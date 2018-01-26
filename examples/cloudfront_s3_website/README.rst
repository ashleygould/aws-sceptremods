Prerequisites:
 - python 2.7 or 3.6
 - aws-sceptremods: https://github.com/ashleygould/aws-sceptremods


Configure a new website::

  cd config/poc
  cp ashley-demo.yaml ricksite.yaml
  perl -pi -e 's/ashley-demo/ricksite/g' ricksite.yaml



Usage::

  sceptre --var-file=config/variables.yaml --debug launch-env poc



Creating initial content::

  bucket_name=cfs3site-bucket-poc-ashley-demo
  aws s3 sync sample_site/ s3://${bucket_name}/

  bucket_name=cfs3site-bucket-qa-ashley-demo
  aws s3 sync sample_site/ s3://${bucket_name}/

