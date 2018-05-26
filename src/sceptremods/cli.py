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
    sceptremods -p PROJECT [-d DIR] [-r REGION]
    sceptremods (--update|--refresh) [-d DIR]

Options:
    -h, --help             Print usage message.
    -v, --version          Print version info.
    -l, --list             Print listing of all template modules in collection.
    -m, --module MODULE    Print documentation for template module MODULE.
    -p, --project PROJECT  Initialize or update a sceptre project.  By default,
                           Populate a new project directory with basic
                           sceptre layout and sceptremods template wrappers.
    --update               Update an existing project with new template wrappers.
    --refresh              Update any wrappers already present in the project.
    -d, --dir DIR          Path to parent directory of a project or the 
                           project directory itself if an existing project.
                           [default: .]
    -r, --region REGION    AWS region for initialized project. [default: us-west-2]

Example:
    sceptremods -p sceptre-myprog -d ~/projects -r us-east-1 
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



def refresh_files(src, dest):
    """
    Update contents of existing 'dest' files from 'src' file
    of same name.
    """
    if not os.path.isdir(src):
        print('Source directory "{}" not found'.format(src))
        sys.exit(1)
    if os.path.isdir(dest):
        files = os.listdir(dest)
        for f in files:
            if os.path.isfile(os.path.join(src, f)):
                shutil.copyfile(os.path.join(src, f), os.path.join(dest, f))
            else:
                print('File "{}" not found in source dir'.format(f))


def recursive_overwrite(src, dest):
    """
    Recursively copy 'src' directory into 'dest' directory.
    Overwrites contents of existing 'dest' files from 'src' file
    of same name.

    example:
        recursive_overwrite(wrappers, sceptre_dir)
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
    project = args['--project']
    wrappers = resource_filename(Requirement.parse('aws-sceptremods'), 'wrappers')

    if not args['--dir']:
        project_dir = os.getcwd()
    else:
        project_dir = os.path.abspath(args['--dir'])
    sceptre_dir = os.path.join(project_dir, 'sceptre')

    if args['--refresh']:
        if not os.path.isdir(sceptre_dir):
            print('sceptre project not found at {}'.format(sceptre_dir))
            sys.exit(1)
        print('refreshing sceptre project at {}'.format(sceptre_dir))
        refresh_files(
            os.path.join(wrappers, 'templates'), 
            os.path.join(sceptre_dir, 'templates')
        )

    elif args['--update']:
        if not os.path.isdir(sceptre_dir):
            print('sceptre project not found at {}'.format(sceptre_dir))
            sys.exit(1)
        print('updating sceptre project at {}'.format(sceptre_dir))
        recursive_overwrite(wrappers, sceptre_dir)

    else:
        if os.path.isdir(sceptre_dir):
            print('sceptre project already exists at {}'.format(sceptre_dir))
            sys.exit(1)
        print('creating new sceptre project "{}" at {}'.format(project, sceptre_dir))
        config_dir = os.path.join(sceptre_dir, 'config')
        config_file = os.path.join(config_dir, 'config.yaml')
        os.makedirs(sceptre_dir)
        os.makedirs(config_dir)
        config = dict(
            project_code='-'.join(['sceptre', project]),
            region=args['--region'],
            sceptremods_version=sceptremods.__version__,
        )
        with open(config_file, 'w') as f:
            yaml.safe_dump(config, stream=f, default_flow_style=False)
        recursive_overwrite(wrappers, sceptre_dir)


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

    if args['--project'] or args['--update'] or args['--refresh']:
        initialize_project(args)

    if args['--module']:
        module_name = args['--module']
        if module_name not in sceptremods.MODULES:
            print('"{}" is not a scetpremods template module'.format(module_name))
            sys.exit(1)
        get_help(module_name)


if __name__ == '__main__':
    main()
