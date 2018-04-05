# -*- coding: utf-8 -*-
import uuid
import re

from sceptre.hooks import Hook
from sceptre.exceptions import InvalidHookArgumentSyntaxError


class Route53HostedZone(Hook):
    """
    Check if the specified route53 hosted zone exists.  If not, create it.
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
        Check if a route53 hosted zone exists for the domain name passed
        in self.arguments.  If not, create it.

        :raises: InvalidHookArgumentSyntaxError, if argument is not a valid 
                 domain name.
        """

        domain_re = re.compile(r'[a-zA-Z\d-]{,63}(\.[a-zA-Z\d-]{,63})*')
        if not (self.argument and domain_re.match(self.argument)):
            raise InvalidHookArgumentSyntaxError(
                'route53_hosted_zone: '
                'argument "{}" is not a valid domain name.'.format(self.argument)
            )

        zone_name = self.argument
        if not zone_name.endswith("."):
            zone_name += "."

        # check if zone already exists
        response = self.stack.connection_manager.call(
            service="route53",
            command="list_hosted_zones",
        )
        hosted_zones = response["HostedZones"]
        while response["IsTruncated"]:
            response = self.stack.connection_manager.call(
                service="route53",
                command="list_hosted_zones",
                kwargs=dict(Marker=reponse["NextMarker"]),
            )
            hosted_zones += response["HostedZones"]
        for zone in hosted_zones:
            if zone["Name"] == zone_name:
                zone_id = self.parse_zone_id(zone["Id"])
                self.logger.debug(
                    '{} - Found hosted zone "{}" with zone id "{}"'.format(
                    __name__, zone_name, zone_id)
                )
                return zone_id

        # create new hosted zone
        reference = uuid.uuid4().hex
        response = self.stack.connection_manager.call(
            service="route53",
            command="create_hosted_zone",
            kwargs=dict(
                Name=zone_name,
                CallerReference=reference,
            )
        )
        zone_id = self.parse_zone_id(response["HostedZone"]["Id"])
        self.logger.debug(
            '{} - Created hosted zone "{}" with zone id "{}"'.format(
            __name__, zone_name, zone_id)
        )
        return zone_id
