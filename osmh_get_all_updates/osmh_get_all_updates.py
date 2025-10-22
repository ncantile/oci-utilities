import oci
import json

config = oci.config.from_file()
compute_client = oci.core.ComputeClient(config)
search_client = oci.resource_search.ResourceSearchClient(config)
osmh_client = oci.os_management_hub.ManagedInstanceClient(config)

wave = input("Insert only the wave number: ")
wave = "wave_" + str(wave)

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
	try:
		#Windows
		response = osmh_client.list_managed_instance_available_windows_updates(
			managed_instance_id = vm,
			classification_type = ["SECURITY"])
		vm_updates = response.data.items
		vm_upd_list = []
		for elem in vm_updates:
			vm_upd_list.append(elem.name)
		all_updates[vm] = vm_upd_list
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
			all_updates[vm] = vm_upd_list
		except:
			#Instance not registered
			continue

json_str = json.dumps(all_updates)
print(json_str)
