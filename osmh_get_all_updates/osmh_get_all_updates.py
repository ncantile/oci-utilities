import oci
import json
import sys

try: 
	wave = "wave_" + str(sys.argv[1])
except:
	wave = input("Insert only the wave number: ")
	wave = "wave_" + str(wave)

config = oci.config.from_file()
compute_client = oci.core.ComputeClient(config)
search_client = oci.resource_search.ResourceSearchClient(config)
osmh_client = oci.os_management_hub.ManagedInstanceClient(config)

def ocid_to_name(ocid):
	res = compute_client.get_instance(
		instance_id = ocid)
	return res.data.display_name
	
print(f"Getting available security updates for all instances in {wave}...")

#Get the OCIDs of all the instances in the wave
search_details = oci.resource_search.models.StructuredSearchDetails(
	type="Structured",
	query=f"query instance resources where (definedTags.namespace = \'patching\' && definedTags.key = \'wave\' && definedTags.value = \'{wave}\')")
search_response = search_client.search_resources(search_details)
instances_in_wave = []
for vm in search_response.data.items:
	instances_in_wave.append(vm.identifier)

all_updates = {}

#Loop through all instances in wave
for vm in instances_in_wave:
	vm_name = ocid_to_name(vm)
	try:
		#Windows
		response = osmh_client.list_managed_instance_available_windows_updates(
			managed_instance_id = vm,
			classification_type = ["SECURITY"])
		vm_updates = response.data.items
		vm_upd_list = []
		for elem in vm_updates:
			vm_upd_list.append(elem.name)
		all_updates[f"{vm_name} ({vm})"] = vm_upd_list
	except:
		try:
			#Linux
			response = osmh_client.list_managed_instance_updatable_packages(
				managed_instance_id = vm,
			classification_type = ["SECURITY"])
			vm_updates = response.data.items
			vm_upd_list = []
			for elem in vm_updates:
				vm_upd_list.append(elem.name)
			all_updates[f"{vm_name} ({vm})"] = vm_upd_list
		except:
			#Instance not registered
			continue

json_str = json.dumps(all_updates)
print(json_str)
