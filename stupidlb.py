#!/usr/bin/env python3
#
# https://kopf.readthedocs.io/en/stable/index.html

import threading
from types import SimpleNamespace
import functools

import kopf
import kubernetes
import logging

MYNAME = 'stupidlb.jorgensen.org.uk'

def valid_ips():
    return {'192.168.0.' + str(x)
            for x in range(224,240)}

LOCK = threading.Lock()

@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.persistence.progress_storage = kopf.AnnotationsProgressStorage(
        prefix=MYNAME)
    settings.persistence.diffbase_storage = kopf.AnnotationsDiffBaseStorage(
        prefix=MYNAME,
        key='last-handled-configuration')

@functools.cache
def k8s():
    """A nice handy way to get a connection to k8s api server"""
    # kubernetes.config.load_kube_config()
    return kubernetes.client.CoreV1Api()

def is_interesting(meta, spec, **_):
    if spec.get('type') != 'LoadBalancer':
        return False
    if meta.get('annotations', {}).get(MYNAME + '/kopf-managed', 'yes') == 'no':
        return False
    if spec.get('externalIPs', []) and spec.get('loadBalancerIP'):
        return False
    return True

@kopf.on.create('Service', when=is_interesting)
@kopf.on.update('Service', when=is_interesting)
def handle_service(meta, spec, logger, **kwargs):
    """Assign an external IP to a service"""
    patch = {}

    # Without locking, things may fail if multiple services need to be
    # handled simultaneously
    with LOCK:
        eips = spec.get('externalIPs', [])
        if not eips:
            eips = [pick_external_ip(meta, spec)]
            patch.setdefault('spec', {})
            patch['spec']['externalIPs'] = eips
            logger.info(f'Assigned external IP {eips[0]}')

        lbip = spec.get('loadBalancerIP')
        if not lbip:
            lbip = eips[0]
            patch.setdefault('spec', {})
            patch['spec']['loadBalancerIP'] = lbip
            logger.info(f'Assigned load balancer IP {lbip}')

        if patch:
            logger.debug(f'Patching: {patch}')
            k8s().patch_namespaced_service(name=meta.name,
                                           namespace=meta.namespace,
                                           body=patch)

def pick_external_ip(meta, spec):
    """Find a free IP address and return it"""
    services = list(eips_in_use(exclude_ns=meta.namespace,
                                exclude_name=meta.name))
    services_dict = {
        svc.ip: svc.namespace + '/' + svc.name
        for svc in services
    }

    avail = valid_ips() - set([svc.ip for svc in services])
    if not avail:
        raise kopf.TemporaryError(f'No free IPs',
                                  delay=60)
    # print(f'available IPs: {avail}')

    lbip = spec.get('loadBalancerIP')
    if lbip:
        if lbip not in avail:
            raise kopf.TemporaryError(f'Cannot use load balancer IP {lbip} - it is in use by {services_dict[lbip]}',
                                      delay=60)
        return lbip

    return avail.pop()

def eips_in_use(exclude_ns:str=None, exclude_name:str=None):
    """Figure out which eips are in use"""
    for service in k8s().list_service_for_all_namespaces(watch=False).items:
        if service.spec.type != 'LoadBalancer':
            continue

        if exclude_ns == service.metadata.namespace and exclude_name == service.metadata.name:
            continue

        if service.spec.load_balancer_ip:
            yield SimpleNamespace(namespace=service.metadata.namespace,
                                  name=service.metadata.name,
                                  ip=service.spec.load_balancer_ip)

        if service.spec.external_i_ps:
            for eip in service.spec.external_i_ps:
                yield SimpleNamespace(namespace=service.metadata.namespace,
                                      name=service.metadata.name,
                                      ip=eip)
