import os
import sys

import sceptremods


class VarSpec(object):

    def __init__(self, name, type, description=None, default=None, validator=None):
        self.name = name
        self.type = type
        self.default = default
        self.description = description
        self.validator = validator

    def describe(self):
        print("{}\n  {}\n  Default: {}\n".format(
                self.name, self.description, self.default))

    def validate(self, user_data):
        if self.name in user_data:
            value = user_data[self.name]
            if not isinstance(value, self.type):
                raise ValueError(
                    "'{}' must be of type {}".format(self.name, self.type)
                )
            if self.validator:
                # exceptions get raised within the validator function
                self.validator(value)
        else:
            if not self.default:
                raise ValueError(
                    "Value of '{}' is undefined and no default is "
                    "specified".format(self.name, self.type)
                )
            user_data[self.name] = self.default


class BaseTemplate(object):
    """Base class for building sceptremods troposphere templates"""

    VARIABLES = dict()

    def __init__(self, user_data, var_spec=VARIABLES):
        self.user_data = user_data
        self.var_spec = _objectify_var_spec(var_spec)

    def _objectify_var_spec(var_spec):
        return [VarSpec(var_name, **attributes)
                for var_name, attributes in var_spec.items()]

    def version(self):
        return sceptremods.__version__

    def help(self):
        print(__doc__)
        print("\nSpecification of spectre_user_data variables for '{}' "
                "template module:\n".format(
                os.path.basename(sys.argv[0].partition('.')[0])))
        for spec in self.var_spec:
            spec.describe()

    def validate_user_data(self):
        for spec in self.var_spec:
            spec.validate(self.user_data)

