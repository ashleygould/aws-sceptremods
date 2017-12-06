import os
import json
import difflib
import importlib
import inspect
from pkg_resources import Requirement, resource_filename

import sceptremods
from sceptremods.templates import BaseTemplate

class InvalidSceptreModError(Exception):
    pass

def diff(a, b):
    """A human readable differ.  Used as error message on failure."""
    return '\n'.join(list(difflib.Differ().compare(a.splitlines(),b.splitlines())))

def as_text(source):
    return json.dumps(source, indent=4, sort_keys=True)

def get_template_fixture(fixture_name):
    """Returns  path to the template fixture file."""
    fixtures_dir = resource_filename(Requirement.parse('aws-sceptremods'),
            'tests/fixtures/templates')
    fixture_file = os.path.join(fixtures_dir, fixture_name + '.json')
    return fixture_file

def template_object(module_name, user_data=dict()):
    """
    Locates the template generator class found in a named sceptremods
    module and returns an instance of that class.
    """
    module = importlib.import_module('sceptremods.templates.' + module_name)
    template_classes = [
            cls for name, cls in inspect.getmembers(module, inspect.isclass)
            if issubclass(cls, BaseTemplate) and cls is not BaseTemplate]
    if len(template_classes) != 1:
        raise InvalidSceptreModError(
                "Module '{}' must contain one and only one superclass "
                "of sceptremods.templates.BaseTemplate.  Classes found: {}".format(
                module_name, template_classes))
    t_class = template_classes[0]
    return t_class(user_data)

def assert_rendered_template(module_name, fixture_name, user_data):
    """
    Renders a template module into a dict, then compares it to a dict loaded
    from the specified template fixture file.
    
    """
    t = template_object(module_name, user_data)
    t.create_template()
    rendered_dict = t.template.to_dict()
    fixture_file = get_template_fixture(fixture_name)
    with open(fixture_file) as fd:
        expected_dict = json.loads(fd.read())
    assert rendered_dict == expected_dict, diff(
            as_text(expected_dict), as_text(rendered_dict))


def generate_template_fixture(module_name, fixture_name, user_data):
    """Generates a fixtures file from template module."""
    t = template_object(module_name, user_data)
    t.create_template()
    rendered_dict = t.template.to_dict()
    fixture_file = get_template_fixture(fixture_name)
    with open(fixture_file + "-gen_fixture", "w") as fd:
        fd.write(as_text(rendered_dict) + '\n')


