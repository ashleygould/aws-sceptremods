#!/usr/bin/env python
'''
CLI for sceptremods

Show listing and docs of modules in the collection.
Generate a new sceptre project.
Stuff like that.

Usage:
    sceptremods (-l | -h | -v)
    sceptremods -m MODULE
    sceptremods --init PROJECT [-r REGION]

Options:
    -h, --help           Print usage message.
    -v, --version        Print version info.
    -l, --list           Print listing of all template modules in collection.
    -m, --module MODULE  Print documentation for template module MODULE.
    --init PROJECT       Initalize a new sceptre project.  This command
                         populates a new project directory with basic
                         sceptre layout and sceptremods wrappers.  The
                         new project directory and sceptre 'project_code'
                         take on the name 'sceptre-${PROJECT}.
    -r, --region REGION  AWS region for initialized project.
'''


import os
import sys
import shutil
import importlib
from inspect import getmembers, isclass
from pkg_resources import Requirement, resource_filename

import yaml
from docopt import docopt

import sceptremods
from sceptremods.templates import BaseTemplate

DEFAULT_REGION = 'us-west-2'


def recursive_overwrite(src, dest):
    """
    Recursively copy 'src' directory into 'dest' directory.
    Overwrites contents of existing 'dest' files from 'src' file
    of same name.
    """
    if os.path.isdir(src):
        if not os.path.isdir(dest):
            os.makedirs(dest)
        files = os.listdir(src)
        for f in files:
            recursive_overwrite(os.path.join(src, f), os.path.join(dest, f))
    else:
        shutil.copyfile(src, dest)


def initialize_project(project, region):
    """
    Generate project directories and populate with sceptremods wrappers.
    Create a project config.yaml file.
    """

    project_dir = os.path.join(os.getcwd(), project)
    config_dir = os.path.join(project_dir, 'config')
    config_file = os.path.join(config_dir, 'config.yaml')

    if not os.path.isdir(project_dir):
        os.makedirs(project_dir)

    if not os.path.isdir(config_dir):
        os.makedirs(config_dir)

    if not os.path.isfile(config_file):
        if not region:
            region = os.environ.get('AWS_DEFAULT_REGION', DEFAULT_REGION)
        config = dict(project_code=project, region=region)
        with open(config_file, 'w') as f:
            yaml.safe_dump(config, stream=f, default_flow_style=False)

    wrappers = resource_filename(Requirement.parse('aws-sceptremods'), 'wrappers')
    recursive_overwrite(wrappers, project_dir)


def get_help(module_name):
    """
    Call the help() method of the sectremods.template class hosted
    by this module.
    """
    module = importlib.import_module('sceptremods.templates.' + module_name)
    template_classes = [cls for name, cls in getmembers(module, isclass)
            if issubclass(cls, BaseTemplate) and cls is not BaseTemplate]
    for cls in template_classes:
        cls().help()


def main():
    args = docopt(__doc__, version='sceptremods %s' % sceptremods.__version__)

    if args['--list']:
        print('sceptremods modules: \n{}'.format('\n'.join(sceptremods.MODULES)))

    if args['--init']:
        initialize_project('sceptre-' + args['--init'], args['--region'])

    if args['--module']:
        module_name = args['--module']
        if module_name not in sceptremods.MODULES:
            print('"{}" is not a scetpremods template module'.format(module_name))
            sys.exit(1)
        get_help(module_name)


if __name__ == '__main__':
    main()
