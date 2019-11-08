# coding: utf-8
# Copyright (c) 2016, 2019, Oracle and/or its affiliates. All rights reserved.

#  This script retrieves all audit logs across an Oracle Cloud Infrastructure Tenancy.
#  for a timespan defined by start_time and end_time.
#  This sample script retrieves Audit events for last 5 days.
#  This script will work at a tenancy level only.

import datetime
import oci

def get_regions(identity, tenancyID):
    '''
    To retrieve the list of all subscribed regions.
    '''
    list_of_regions = []
    response = identity.list_region_subscriptions(tenancyID)
    regions = response.data
    for r in regions:
        list_of_regions.append(r)
    return list_of_regions


def get_tags(identity, RootCompartmentID):
    '''
    To retrieve a list of all active Tag Namespaces and the collection of tags in each
    '''
    customertags = []
    tag_response = identity.list_tag_namespaces(RootCompartmentID)
    tags_namespaces = tag_response.data
    for namespace in tags_namespaces:
      tagresponse = identity.list_tags(namespace.id)
      tags = tagresponse.data
      for tag in tags:
        if (tag.lifecycle_state == 'ACTIVE'):
          customertags.append([namespace.name,tag.name])
    return customertags

def get_compartments(identity, tenancy_id):
    '''
    Retrieve the list of compartments (name, ocid) under the specified tenancy/compartment
      Revised - returns OCI structure
    '''
    comp_list = []
    response = identity.list_compartments(tenancy_id)
    compartments = response.data
    for compartment in compartments:
      comp_list.append(compartment)
    return comp_list

def get_compute(config, compartment):
    '''
    retrieve a list of compute instances for a specific AD in the region
    '''
    compute = []
    compute_client = oci.core.ComputeClient(config)
    response = compute_client.list_instances(compartment)
    compute_data = response.data
    for compute_instance in compute_data:
       compute.append(compute_instance)
    return compute

def get_block_storage(identity, config, compartment):
    '''
    retrieve a list of block storage for a specific AD in the region
    '''
    blockstorage = []
    storage_client = oci.core.BlockstorageClient(config)
    response = identity.list_availability_domains(compartment)
    domains = response.data
    for domain in domains: 
      response = storage_client.list_boot_volumes(domain.name, compartment)
      blockvolumes = response.data
      for volume in blockvolumes:
        blockstorage.append (volume)
    return blockstorage


def get_audit_events(audit, compartment_ocids, start_time, end_time):
    '''
    Get events iteratively for each compartment defined in 'compartments_ocids'
    for the region defined in 'audit'.
    This method eagerly loads all audit records in the time range and it does
    have performance implications of lot of audit records.
    Ideally, the generator method in oci.pagination should be used to lazily
    load results.
    '''
    list_of_audit_events = []
    for c in compartment_ocids:
        list_events_response = oci.pagination.list_call_get_all_results(
            audit.list_events,
            compartment_id=c,
            start_time=start_time,
            end_time=end_time).data

        #  Results for a compartment 'c' for a region defined
        #  in 'audit' object.
        list_of_audit_events.extend(list_events_response)
        return list_of_audit_events

