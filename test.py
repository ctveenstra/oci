# coding: utf-8
# Copyright (c) 2016, 2019, Oracle and/or its affiliates. All rights reserved.


# goal: to locate billable resources across the compartments, and then determine if they have tags correctly assigned to them
# 
#  for each compartment
#    for each region
#      for each AD
#        for each resource (compute, block volume, etc.)
#          if !tag
#            fetch audit records based on creation time of the resource
#            identify the creator ocid
#            update the resource defined-tags with the creator username
#          end if
#        end for
#      end for
#    end for
#  end for

import sys
import requests
import oci
from helper import *

# load the OCI configuration 
config = oci.config.from_file()

# get the RootCompartmentID
identity = oci.identity.IdentityClient(config)
user = identity.get_user(config["user"]).data
RootCompartmentID = user.compartment_id
tenancyID = config["tenancy"]

print ("Logged in as: {} @ {}\n".format(user.description, config["region"]))

regions = get_regions(identity, tenancyID)
for region in regions:
  print ("- {}".format(region.region_name))
print("\n")

# Get the list of compartments available
compartment_list=get_compartments(identity, RootCompartmentID)
for compartment in compartment_list:
   print("Compartment:  {}  {}".format(("("+compartment.lifecycle_state+ ")").ljust(9), compartment.name ))

   # get list of compute instances (testing)
   compute=get_compute(config, compartment.id)
   for instance in compute:
      if ("UCM_Resource_Ownership" in instance.defined_tags.keys()):
        print("   compute: {} - {} - {} - {}".format(compartment.name, instance.availability_domain, instance.display_name, instance.defined_tags['UCM_Resource_Ownership']['Owner']))
      else:
        print("   compute: {} - {} - {} - {}".format(compartment.name, instance.availability_domain, instance.display_name, "Tag not defined"))

   blockstorage = get_block_storage(identity, config, compartment.id)
   for block in blockstorage:
      if("UCM_Resource_Ownership" in block.defined_tags.keys()):
        print("   block volume: {} - {} - {}".format(block.availability_domain, block.display_name, block.defined_tags['UCM_Resource_Ownership']['Owner']))
      else:
        print("   block volume: {} - {} - {}".format(block.availability_domain, block.display_name, "Tag not defined"))
  
print("\n")
