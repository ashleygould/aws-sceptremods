"""Ruthlessly ripped from stacker.util (https://github.com/remind101/stacker)"""

import logging
import uuid
import copy
from six import string_types

from sceptre.hooks import Hook
from sceptre.exceptions import InvalidHookArgumentTypeError
from sceptre.exceptions import InvalidHookArgumentSyntaxError
from sceptre.exceptions import InvalidHookArgumentValueError




logger = logging.getLogger(__name__)




class Route53(Hook):
    """
    TODO: approprieat comments
    """

    def __init__(self, *args, **kwargs):
        super(Route53, self).__init__(*args, **kwargs)

    def run(self):
        """
        TODO: approprieat comments

        :raises: InvalidHookArgumentTypeError, if argument is not a string.
        """

        if not isinstance(self.argument, string_types):
            raise InvalidHookArgumentTypeError(
                'The argument "{0}" is the wrong type - route53_zone '
                'hook requires arguments of type string.'.format(self.argument)
            )

        domain = kwargs.get("domain")
        if not domain:
            logger.error("domain argument or BaseDomain variable not provided.")
            return False
        zone_id = self.create_route53_zone(client, domain)
        return {"domain": domain, "zone_id": zone_id}

        #self.connection_manager.call(
        #    service="route53",
        #    command=action,
        #    kwargs={
        #        "AutoScalingGroupName": autoscaling_group,
        #        "ScalingProcesses": [scaling_processes]
        #    }
        #)



def parse_zone_id(full_zone_id):
    """Parses the returned hosted zone id and returns only the ID itself."""
    return full_zone_id.split("/")[2]


def get_hosted_zone_by_name(client, zone_name):
    """Get the zone id of an existing zone by name.

    Args:
        client (:class:`botocore.client.Route53`): The connection used to
            interact with Route53's API.
        zone_name (string): The name of the DNS hosted zone to create.

    Returns:
        string: The Id of the Hosted Zone.
    """
    p = client.get_paginator("list_hosted_zones")

    for i in p.paginate():
        for zone in i["HostedZones"]:
            if zone["Name"] == zone_name:
                return parse_zone_id(zone["Id"])
    return None


def get_or_create_hosted_zone(client, zone_name):
    """Get the Id of an existing zone, or create it.

    Args:
        client (:class:`botocore.client.Route53`): The connection used to
            interact with Route53's API.
        zone_name (string): The name of the DNS hosted zone to create.

    Returns:
        string: The Id of the Hosted Zone.
    """
    zone_id = get_hosted_zone_by_name(client, zone_name)
    if zone_id:
        return zone_id

    logger.debug("Zone %s does not exist, creating.", zone_name)

    reference = uuid.uuid4().hex

    response = client.create_hosted_zone(Name=zone_name,
                                         CallerReference=reference)

    return parse_zone_id(response["HostedZone"]["Id"])




class SOARecordText(object):
    """Represents the actual body of an SOARecord. """
    def __init__(self, record_text):
        (self.nameserver, self.contact, self.serial, self.refresh,
            self.retry, self.expire, self.min_ttl) = record_text.split()

    def __str__(self):
        return "%s %s %s %s %s %s %s" % (
            self.nameserver, self.contact, self.serial, self.refresh,
            self.retry, self.expire, self.min_ttl
        )


class SOARecord(object):
    """Represents an SOA record. """
    def __init__(self, record):
        self.name = record["Name"]
        self.text = SOARecordText(record["ResourceRecords"][0]["Value"])
        self.ttl = record["TTL"]


def get_soa_record(client, zone_id, zone_name):
    """Gets the SOA record for zone_name from zone_id.

    Args:
        client (:class:`botocore.client.Route53`): The connection used to
            interact with Route53's API.
        zone_id (string): The AWS Route53 zone id of the hosted zone to query.
        zone_name (string): The name of the DNS hosted zone to create.

    Returns:
        :class:`stacker.util.SOARecord`: An object representing the parsed SOA
            record returned from AWS Route53.
    """

    response = client.list_resource_record_sets(HostedZoneId=zone_id,
                                                StartRecordName=zone_name,
                                                StartRecordType="SOA",
                                                MaxItems="1")
    return SOARecord(response["ResourceRecordSets"][0])


def create_route53_zone(client, zone_name):
    """Creates the given zone_name if it doesn't already exists.

    Also sets the SOA negative caching TTL to something short (300 seconds).

    Args:
        client (:class:`botocore.client.Route53`): The connection used to
            interact with Route53's API.
        zone_name (string): The name of the DNS hosted zone to create.

    Returns:
        string: The zone id returned from AWS for the existing, or newly
            created zone.
    """
    if not zone_name.endswith("."):
        zone_name += "."
    zone_id = get_or_create_hosted_zone(client, zone_name)
    old_soa = get_soa_record(client, zone_id, zone_name)

    # If the negative cache value is already 300, don't update it.
    if old_soa.text.min_ttl == "300":
        return zone_id

    new_soa = copy.deepcopy(old_soa)
    logger.debug("Updating negative caching value on zone %s to 300.",
                 zone_name)
    new_soa.text.min_ttl = "300"
    client.change_resource_record_sets(
        HostedZoneId=zone_id,
        ChangeBatch={
            "Comment": "Update SOA min_ttl to 300.",
            "Changes": [
                {
                    "Action": "UPSERT",
                    "ResourceRecordSet": {
                        "Name": zone_name,
                        "Type": "SOA",
                        "TTL": old_soa.ttl,
                        "ResourceRecords": [
                            {
                                "Value": str(new_soa.text)
                            }
                        ]
                    }
                },
            ]
        }
    )
    return zone_id


