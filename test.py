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

import requests
import oci

config = oci.config.from_file()
auth = oci.signer.Signer(
    tenancy=config['tenancy'],
    user=config['user'],
    fingerprint=config['fingerprint'],
    private_key_file_location=config['key_file'],
    pass_phrase=config['pass_phrase']
)

# get the RootCompartmentID
identity = oci.identity.IdentityClient(config)
user = identity.get_user(config["user"]).data
RootCompartmentID = user.compartment_id

print ("Logged in as: {} @ {}\n".format(user.description, config["region"]))

print ("Querying Enabled Regions:")
response = identity.list_region_subscriptions(config["tenancy"])
regions = response.data

for region in regions:
  if region.is_home_region:
    home = "Home region"
  else:
    home = ""
  print ("- {} ({}) {}".format(region.region_name, region.status, home))

# Get all the predefined tags, so the initial header line can be created.
print ("\nDefined Tags:")
customertags = []
response = identity.list_tag_namespaces(RootCompartmentID)
tags_namespaces = response.data
for namespace in tags_namespaces:
  tagresponse = identity.list_tags(namespace.id)
  tags = tagresponse.data
  for tag in tags:
    if (tag.lifecycle_state == 'ACTIVE'):
      customertags.append([namespace.name,tag.name])
      print("- {} - {} ({})".format(namespace.name, tag.name, tag.lifecycle_state))

# Get all the compartments
print ("\nCompartments:")
response = identity.list_compartments(RootCompartmentID)
compartments = response.data  
for compartment in compartments:
  if (compartment.name.startswith('nat-ea')):
    print ("- {}".format(compartment.name))

    for region in regions:
      r = {"region": region.region_name}
      print ("Region: {}".format(region.region_name))
      config.update(r)
      identity = oci.identity.IdentityClient(config)

      compute = oci.core.ComputeClient(config)
      response = compute.list_instances(compartment.id)
      instances = response.data
      for instance in instances:
        # determine if the defined tag is set
        if("UCM_Resource_Ownership" in instance.defined_tags.keys()):
          print ("  {} - Compute     -> {} ({}) {}".format(instance.availability_domain, instance.display_name, instance.lifecycle_state, instance.defined_tags['UCM_Resource_Ownership']['Owner']))
        else:
          print ("  {} - Compute     -> {} ({}) {}".format(instance.availability_domain, instance.display_name, instance.lifecycle_state, " -> Tag not defined"))

      # AD specific resources

      response = identity.list_availability_domains(compartment.id)
      domains = response.data

      for domain in domains:
        print("Domain: {}".format(domain.name))
        blockstorage = oci.core.BlockstorageClient(config)
        response = blockstorage.list_boot_volumes(domain.name, compartment.id)
        blockvolumes = response.data
        for volume in blockvolumes:
          # determine if the defined tag is set
          if("UCM_Resource_Ownership" in volume.defined_tags.keys()):
            print ("  {} - Boot Volume -> {} ({}) {}".format(domain.name, volume.display_name.replace(' (Boot Volume)',''), volume.lifecycle_state, volume.defined_tags['UCM_Resource_Ownership']['Owner']))
          else:
            print ("  {} - Boot Volume -> {} ({}) {}".format(domain.name, volume.display_name.replace(' (Boot Volume)',''), volume.lifecycle_state, " -> Tag not defined"))
        
   
print("\n")
