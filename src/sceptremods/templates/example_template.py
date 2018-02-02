"""This is a example sceptremods module to use as a base template to copy 
from when creating a new sceptremod module."""

import sys

from troposphere import (
    GetAtt,
    Join,
    Output,
    Ref,
    ec2,
)

from sceptremods.templates import BaseTemplate


#
# The template class
#
class Example(BaseTemplate):
    """Example sceptremods class.  Builds an empty template."""

    VARSPEC = {
        'MyVar': {
            'type': str,
            'default': 'blee',
            'description': 'Value of MyVar.',
        },
    }

    def create_template(self):
        self.vars = self.validate_user_data()
        t = self.template
        # your resources defined here


#
# The sceptre handler
#
def sceptre_handler(sceptre_user_data):
    example = Example(sceptre_user_data)
    example.create_template()
    return example.template.to_json()

def main():
    """
    When called as a script, print out the generated template.
    If any arg is supplied, call the template class help method.
    """
    if len(sys.argv) > 1:
        Example().help()
    else:
        print(sceptre_handler(dict()))

if __name__ == '__main__':
    main()

