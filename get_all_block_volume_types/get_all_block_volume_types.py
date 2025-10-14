#!/bin/python3

# This script outputs a list of all the block volumes which are attached to any instance
# and the respective attachment type (Paravirtualized or iSCSI)

import oci
import time
import sys

print("instance_name,volume_id,volume_name,device,type")

config = oci.config.from_file()
tenancy_id = config["tenancy"]

iam_client = oci.identity.IdentityClient(config)
storage_client = oci.core.BlockstorageClient(config)
compute_client = oci.core.ComputeClient(config)

# Search all compartments
all_compartments = [tenancy_id]
response = iam_client.list_compartments(
	tenancy_id,
	compartment_id_in_subtree=True,
	access_level="ANY"
	)
for c in response.data:
	all_compartments.append(c.id)

for c in all_compartments:
	attachments = compute_client.list_volume_attachments(compartment_id = c).data
	for a in attachments:
		instance_name = compute_client.get_instance(instance_id = a.instance_id)
		try:
			volume_name = storage_client.get_volume(volume_id = a.volume_id).data.display_name
		except:
			volume_name = storage_client.get_boot_volume(boot_volume_id = a.volume_id).data.display_name
		finally:
			print(f"{instance_name},{a.volume_id},{volume_name},{a.device},{a.attachment_type}")
