# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import boto3
from botocore.exceptions import ClientError

from sceptre.hooks import Hook
from sceptre.exceptions import SceptreException
from sceptre.exceptions import InvalidHookArgumentSyntaxError
from sceptre.cli import setup_logging


class ZappaLambda(Hook):
    """
    Deploy/Update Lambda function in AWS using Zappa.

    lambda_path is relative to sceptre project base dir.
    """

    def __init__(self, *args, **kwargs):
        super(ZappaLambda, self).__init__(*args, **kwargs)

    def run(self):
        if len(self.argument.split()) == 3:
            zappa_cmd, zappa_dir, stage_env = self.argument.split()
        else:
            raise InvalidHookArgumentSyntaxError(
                '{}: hook requires three positional parameters: '
                'zappa_cmd', 'zappa_dir, stage_env'.format( __name__)
            )
        if zappa_cmd not in ['deploy', 'update']:
            raise InvalidHookArgumentSyntaxError(
                '{}: first arg must be one of "deploy" or "update"'.format(__name__)
            )

        os.chdir(zappa_dir)
        proc = subprocess.run([
            'zappa', 
            zappa_cmd,
            stage_env,
            '--disable_progress',
            ],
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
        )
        if proc.returncode == 0:
            self.logger.debug(
                "{} - lambda function {} successful. {}".format(
                __name__, zappa_cmd, proc.stdout.decode('utf-8'))
            )
        else:
            errmsg = proc.stderr.decode('utf-8').rstrip()
            self.logger.debug("{} - Failed with return code: {}".format(
                __name__, proc.returncode)
            )
            self.logger.debug("{} - {}".format(__name__, errmsg)) 

def main():
    """
    Hook validation.  

    Usage:
        python zappa_deploy_lambda.py <deploy|update> ../zappa prod
    """
    print(sys.argv)
    request = ZappaLambda(argument=' '.join(sys.argv[1:]))
    request.logger = setup_logging(True, False)
    request.run()


if __name__ == '__main__':
    main()

