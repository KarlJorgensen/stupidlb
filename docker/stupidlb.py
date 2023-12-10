#!/usr/bin/env python3
#
# https://kopf.readthedocs.io/en/stable/index.html
"""Simple Stupid Load Balancer Operator

This will assign external IPs and LoadbalancerIPs on services which do
not have them from a pool of IP addresses.

This will not _actually_ create an external load balancer; it is
assumed that the IP addresses in the pool are valid for the local
network (and wont conflict with anything else - e.g. DHCP-assigned
addresses).

"""

import functools
import ipaddress
import logging
import threading
import os

import kopf
import kubernetes

MYNAME = 'stupidlb.jorgensen.org.uk'

@functools.cache
def valid_ips():
    """Return a set of valid IP addresses we can pick from

    This is the total set of IP addresses reserved for the operator to
    assign from.

    """
    cidrs = os.environ.get('CIDRS')
    if not cidrs:
        raise ValueError('Environment variable CIDRS is not set. We need that.')

    res = set()
    for network in [ipaddress.IPv4Network(cidr)
                    for cidr in cidrs.split(',')]:
        res |= {str(h) for h in network.hosts()}
        # network.hosts() excludes these by default
        res |= {str(network.network_address), str(network.broadcast_address)}

    return res

LOCK = threading.Lock()

@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    """Startup hook

    See https://kopf.readthedocs.io/en/stable/startup/
    """
    settings.persistence.progress_storage = kopf.AnnotationsProgressStorage(
        prefix=MYNAME)
    settings.persistence.diffbase_storage = kopf.AnnotationsDiffBaseStorage(
        prefix=MYNAME,
        key='last-handled-configuration')
    settings.posting.level = logging.WARN

    if not valid_ips():
        raise ValueError('No valid IP ranges!?')
    print(f'Valid IPs: {valid_ips()}')

@functools.cache
def k8s():
    """A nice handy way to get a connection to k8s api server"""
    # kubernetes.config.load_kube_config()
    return kubernetes.client.CoreV1Api()

def is_interesting(meta, spec, **_):
    """Whether we want to handle a given k8s resource

    We only deal with LoadBalancer type services.

    The user may annotate a service to be ignored by the operator.

    We only care about services without IP addresses. Thus if the user
    manually sets an IP address, we do not override it.

    """
    if spec.get('type') != 'LoadBalancer':
        return False
    if meta.get('annotations', {}).get(MYNAME) == 'ignore':
        return False
    if meta.get('annotations', {}).get(MYNAME + '/kopf-managed', 'yes') == 'no':
        return False
    if spec.get('externalIPs', []) and spec.get('loadBalancerIP'):
        return False
    return True

@kopf.on.create('Service', when=is_interesting)
@kopf.on.update('Service', when=is_interesting)
def handle_service(meta, spec, logger, patch, **_):
    """Assign an external IP to a service"""

    # Without locking, things may fail if multiple services need to be
    # handled simultaneously
    with LOCK:
        eips = spec.get('externalIPs', [])
        if not eips:
            eips = [pick_external_ip(meta, spec, logger)]
            patch.spec['externalIPs'] = eips
            logger.info(f'Assigned external IP {eips[0]}')

        lbip = spec.get('loadBalancerIP')
        if not lbip:
            lbip = eips[0]
            patch.spec['loadBalancerIP'] = lbip
            logger.info(f'Assigned load balancer IP {lbip}')

def pick_external_ip(meta, spec, logger):
    """Find a free IP address and return it"""
    used = set(ips_in_use(exclude_ns=meta.namespace,
                          exclude_name=meta.name))
    logger.debug(f'{used=}')

    avail = valid_ips() - used
    if not avail:
        raise kopf.TemporaryError('No free IPs',
                                  delay=60)
    logger.debug(f'{avail=}')

    lbip = spec.get('loadBalancerIP')
    if lbip:
        if lbip in avail:
            return lbip

        if lbip not in valid_ips():
            raise kopf.TemporaryError(
                f'loadBalancerIP {lbip} is not valid with current {MYNAME} config',
                delay=60)

        raise kopf.TemporaryError(f'loadBalancerIP {lbip} is valid but already in use',
                                  delay=60)

    return avail.pop()

def ips_in_use(exclude_ns:str=None, exclude_name:str=None):
    """Figure out which IP addresses are in use elsewhere

    """
    for service in k8s().list_service_for_all_namespaces(watch=False).items:
        if service.spec.type != 'LoadBalancer':
            continue

        if exclude_ns == service.metadata.namespace and exclude_name == service.metadata.name:
            continue

        if service.spec.load_balancer_ip:
            yield service.spec.load_balancer_ip

        if service.spec.external_i_ps:
            yield from service.spec.external_i_ps
