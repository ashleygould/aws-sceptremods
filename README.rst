

Usage Examples
--------------

::

  sceptre  validate-template test vpc
  sceptre  generate-template test vpc
  sceptre  generate-template test vpc > scratch && json2yaml.sh scratch && rm scratch

  sceptre launch-env test

ashley-sceptre_project> sceptre --debug --dir example launch-env test
