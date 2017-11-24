# -*- coding: utf-8 -*-
import uuid
import re
from six import string_types

from sceptre.hooks import Hook
from sceptre.exceptions import InvalidHookArgumentTypeError
from sceptre.exceptions import InvalidHookArgumentSyntaxError


class Route53HostedZone(Hook):
    """
    TODO: approprieat comments
    """

    def __init__(self, *args, **kwargs):
        super(Route53HostedZone, self).__init__(*args, **kwargs)

    def parse_zone_id(self, full_zone_id):
        """
        Parses the returned hosted zone id and returns only the ID itself.
        """
        return full_zone_id.split("/")[2]

    def run(self):
        """
        TODO: approprieat comments

        :raises: InvalidHookArgumentTypeError, if argument is not a string.
        :raises: InvalidHookArgumentSyntaxError, if argument is not a valid 
                 domain name.
        """

        if not isinstance(self.argument, string_types):
            raise InvalidHookArgumentTypeError(
                'The argument "{0}" is the wrong type - route53_hosted_zone '
                'hook requires arguments of type string.'.format(self.argument)
            )

        domain_re = re.compile(r'[a-zA-Z\d-]{,63}(\.[a-zA-Z\d-]{,63})*')
        if not domain_re.match(self.argument):
            raise InvalidHookArgumentSyntaxError(
                'The argument "{}" is not valid - route53_hosted_zone '
                'hook requires argument must be a valid domain name.'
            )

        zone_name = self.argument
        if not zone_name.endswith("."):
            zone_name += "."

        # check if zone already exists
        response = self.connection_manager.call(
            service="route53",
            command="list_hosted_zones",
        )
        # TODO: check for NextMarker in response
        for zone in response["HostedZones"]:
            if zone["Name"] == zone_name:
                self.logger.debug('found zone_id: {}'.format(zone["Id"]))
                return self.parse_zone_id(zone["Id"])

        # create new hosted zone
        reference = uuid.uuid4().hex
        response = self.connection_manager.call(
            service="route53",
            command="create_hosted_zone",
            kwargs=dict(
                Name=zone_name,
                CallerReference=reference,
            )
        )
        self.logger.debug('created zone_id: {}'.format(response["HostedZone"]["Id"]))
        return self.parse_zone_id(response["HostedZone"]["Id"])
