#!/usr/bin/env python
'''
CLI for sceptremods

Show listing of modules in the collection.
Print documentation for a specific module.
Generate a new sceptre project.
Update an existing secptre project.
Stuff like that.

Usage:
    sceptremods (-l | -h | -v)
    sceptremods -m MODULE
    sceptremods --init PROJECT [-d DIR] [-r REGION]
    sceptremods --update PROJECT [-d DIR]

Options:
    -h, --help           Print usage message.
    -v, --version        Print version info.
    -l, --list           Print listing of all template modules in collection.
    -m, --module MODULE  Print documentation for template module MODULE.
    --init PROJECT       Initalize a new sceptre project.  This command
                         populates a new project directory with basic
                         sceptre layout and sceptremods wrappers.
    --update PROJECT     Update an existing project with new wrappers.
    -d, --dir DIR        Path to parent directory of a project or the 
                         project directory itself if an existing project.
                         [default: .]
    -r, --region REGION  AWS region for initialized project. [default: us-west-2]

Example:
    sceptremods --init -d ~/projects -r us-east-1 sceptre-myprog
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


def initialize_project(args):
    """
    Generate project directories or update existing project.
    """
    if args['--init']:
        project = args['--init']
    else:
        project = args['--update']

    if not args['--dir']:
        base_dir = os.getcwd()
    else:
        base_dir = os.path.abspath(args['--dir'])
        if not os.path.isdir(base_dir):
            print('Directory "{}" not found'.format(base_dir))
            sys.exit(1)

    print(base_dir)
    if os.path.basename(base_dir) == project:
        project_dir = os.path.join(base_dir)
    else:
        project_dir = os.path.join(base_dir, project)

    if args['--update']:
        if not os.path.isdir(project_dir):
            print('project "{}" not found at {}'.format(project, project_dir))
            sys.exit(1)
        print('updating existing project "{}" at {}'.format(project, project_dir))
    else:
        if os.path.isdir(project_dir):
            print('project "{}" already exists at {}'.format(project, project_dir))
            sys.exit(1)
        print('creating new project "{}" at {}'.format(project, project_dir))
        config_dir = os.path.join(project_dir, 'config')
        config_file = os.path.join(config_dir, 'config.yaml')
        os.makedirs(project_dir)
        os.makedirs(config_dir)
        config = dict(
            project_code=project, 
            region=args['--region'],
            sceptremods_version=sceptremods.__version__,
        )
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
    #print(args)

    if args['--list']:
        print('sceptremods modules: \n{}'.format('\n'.join(sceptremods.MODULES)))

    if args['--init'] or args['--update']:
        initialize_project(args)

    if args['--module']:
        module_name = args['--module']
        if module_name not in sceptremods.MODULES:
            print('"{}" is not a scetpremods template module'.format(module_name))
            sys.exit(1)
        get_help(module_name)


if __name__ == '__main__':
    main()
