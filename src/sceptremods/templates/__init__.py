"""
sceptremods.templates provides two base classes:
sceptremods.templates.VarSpec
sceptremods.templates.BaseTemplate
"""

import os
import os
import sys
import types
import abc
from inspect import getmodule, getmodulename, getdoc

from troposphere import Template
import sceptremods


class VarSpec(object):
    __metaclass__ = abc.ABCMeta

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
                if not isinstance(self.validator, types.FunctionType):
                    raise RuntimeError(
                        "Invalid VARSPEC entry '{}'. Value of 'validator' "
                        "must be a function".format(self.name)
                    )
                # ValurError exceptions get raised in the validator function
                self.validator(value)
        else:
            if self.default == None:
                raise RuntimeError(
                    "Value of '{}' is undefined and no default is "
                    "specified".format(self.name, self.type)
                )
            if not isinstance(self.default, self.type):
                raise RuntimeError(
                    "Invalid VARSPEC entry '{}'. Value of 'default' "
                    "must be of type {}".format(self.name, self.type)
                )
            user_data[self.name] = self.default



class BaseTemplate(object):
    """Base class for building sceptremods troposphere templates"""

    __metaclass__ = abc.ABCMeta
    VARSPEC = {}

    def __init__(self, user_data=dict()):
        self.template = Template()
        self.user_data = user_data
        self.var_spec = [VarSpec(var_name, **attributes)
                for var_name, attributes in self.VARSPEC.items()]

    def validate_user_data(self):
        for var in self.user_data.keys():
            if var not in [spec.name for spec in self.var_spec]:
                raise ValueError("Variable '{}' is not defined in VARSPEC "
                "for this template module".format(var))
        for spec in self.var_spec:
            spec.validate(self.user_data)
        return self.user_data

    def version(self):
        return sceptremods.__version__

    def help(self):
        module = getmodule(self)
        module_name = getmodulename(module.__file__)
        class_name = self.__class__.__name__

        print('\nSceptremods Version: {}\n'.format(self.version()))
        print('Module: {}'.format(module_name))
        if getdoc(module): print('{}/n'.format(getdoc(module)))

        print('Class: {}'.format('.'.join([module_name, class_name])))
        if getdoc(self): print('{}/n'.format(getdoc(self)))
        print("Specification of spectre_user_data variables:\n")
        for spec in self.var_spec:
            spec.describe()

