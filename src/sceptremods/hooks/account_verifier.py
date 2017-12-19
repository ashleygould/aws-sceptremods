# -*- coding: utf-8 -*-
import re

from sceptre.hooks import Hook
from sceptre.exceptions import SceptreException
from sceptre.exceptions import InvalidHookArgumentSyntaxError


class AccountVerifier(Hook):
    """
    Test if the Id of currently authenticated AWS account matches
    the specified account Id.  
    """

    def __init__(self, *args, **kwargs):
        super(AccountVerifier, self).__init__(*args, **kwargs)

    def run(self):
        """
        Compare argument to AWS Account Id.

        :raises: InvalidHookArgumentSyntaxError, if argument is not a valid 
                 AWS Account Id.
        """

        account_id_re = re.compile(r'\d{12}')
        if not (self.argument and account_id_re.match(self.argument)):
            raise InvalidHookArgumentSyntaxError(
                '{}: argument "{}" is not a valid AWS account Id.'.format(
                    __name__, self.argument
                )
            )

        response = self.connection_manager.call(
            service="sts",
            command="get_caller_identity",
        )
        account_id = response["Account"]

        if not account_id == self.argument:
            raise SceptreException(
                '{}: account verification failed - current account "{}" does '
                'not match specified account Id "{}".'.format(
                    __name__, account_id, self.argument
                )
            )
        else:
            self.logger.debug(
                '{} - verification succeeded for Id {}'.format(__name__, account_id)
            )
            return True
