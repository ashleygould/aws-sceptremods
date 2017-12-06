import os
import difflib
import json
from pkg_resources import Requirement, resource_filename


def fixtures_dir():
    """Returns  path to the template fixtures directory."""
    return resource_filename(Requirement.parse('aws-sceptremods'),
            'tests/fixtures/templates')

def diff(a, b):
    """A human readable differ.  Used as error message on failure."""
    return '\n'.join(list(difflib.Differ().compare(a.splitlines(),b.splitlines())))

def assert_rendered_template(template, name, gen_fixture):
    """
    Renders template into a dict, then compares it to a dict loaded
    from json fixtures file.

    If 'gen_fixture' is set, instead regenerates a fixtures file
    from template.
    
    :template       a sceptremods template object
    :name           name of the fixture to test against
    :gen_fixture    whether to generate a new fixture file from template
    """

    fixture_file = os.path.join(fixtures_dir(), name + '.json')
    rendered_dict = template.template.to_dict()
    rendered_text = json.dumps(rendered_dict, indent=4, sort_keys=True)

    if gen_fixture:
        with open(fixture_file + "-gen_fixture", "w") as fd:
            fd.write(rendered_text + '\n')
    else:
        with open(fixture_file) as fd:
            expected_dict = json.loads(fd.read())
            expected_text = json.dumps(expected_dict, indent=4, sort_keys=True)
        assert rendered_dict == expected_dict, diff(rendered_text, expected_text)

