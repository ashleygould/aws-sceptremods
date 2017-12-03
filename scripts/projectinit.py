#!/usr/bin/env python
'''
Populate a new project directory with basic sceptre layout and 
sceptremods wrappers.

The new project directory and sceptre 'project_code' take on the
name 'sceptre-project-${PROJECT}

Usage:
    sceptremods (--help | --version)
    sceptremods init PROJECT [--region REGION]

Options:
    --help, -h                  Print usage.
    --version, -v               Print version.
    PROJECT                     Name of the project.
    --region REGION, -r REGION  AWS region.
'''


import os
import sys
import shutil
from pkg_resources import Requirement, resource_filename

import yaml
from docopt import docopt

import sceptremods


DEFAULT_REGION = 'us-west-2'


def recursive_overwrite(src, dest):
    """
    Recursivelt copy 'src' directory into 'dest' directory.
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


def main():
    args = docopt(__doc__)

    if args['--version']:
        print(sceptremods.__version__)

    if args['PROJECT']:
        project = 'sceptre-project-' + args['PROJECT']
        project_dir = os.path.join(os.getcwd(), project)
        config_dir = os.path.join(project_dir, 'config')
        config_file = os.path.join(config_dir, 'config.yaml')

        if not os.path.isdir(project_dir):
            os.makedirs(project_dir)
        if not os.path.isdir(config_dir):
            os.makedirs(config_dir)

        if not os.path.isfile(config_file):
            if args['--region']:
                region = args['--region']
            else:
                region = os.environ.get('AWS_DEFAULT_REGION', DEFAULT_REGION)
            config = dict(project_code=project, region=region)
            with open(config_file, 'w') as f:
                yaml.safe_dump(config, stream=f, default_flow_style=False)

        wrappers = resource_filename(
                Requirement.parse('aws-sceptremods'), 'wrappers')
        recursive_overwrite(wrappers, project_dir)


if __name__ == '__main__':
    main()
