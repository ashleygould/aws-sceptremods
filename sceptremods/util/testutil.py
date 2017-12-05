"""Shamelessly copied from stacker.templates.testutil"""

import difflib
import json
import unittest


def diff(a, b):
    """A human readable differ.
    Used by assertEqual() as error message on failure.
    """
    return '\n'.join(
        list(
            difflib.Differ().compare(
                a.splitlines(),
                b.splitlines()
            )
        )
    )


class TemplateTestCase(unittest.TestCase):
    OUTPUT_PATH = "tests/fixtures/templates"

    def assertRenderedTemplate(self, template, name):
        """renders template into a dict, then compares it to a
        dict loaded from json fixtures file."""
        expected_output = "%s/%s.json" % (self.OUTPUT_PATH, name)

        rendered_dict = template.template.to_dict()
        rendered_text = json.dumps(rendered_dict, indent=4, sort_keys=True)

        ## useful for generating fixture templates
        #with open(expected_output + "-result", "w") as fd:
        #    fd.write(rendered_text)

        with open(expected_output) as fd:
            expected_dict = json.loads(fd.read())
            expected_text = json.dumps(expected_dict, indent=4, sort_keys=True)

        self.assertEqual(rendered_dict, expected_dict,
                          diff(rendered_text, expected_text))




