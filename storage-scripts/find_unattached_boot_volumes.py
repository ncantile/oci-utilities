#!/bin/python3
import oci

#Create the identity client
config = oci.config.from_file()
iam_client = oci.identity.IdentityClient(config)
storage_client = oci.core.BlockstorageClient(config)
compute_client = oci.core.ComputeClient(config)
tenancyOCID = config["tenancy"]

def printTable(myDict, colList=None):
	""" Pretty print a list of dictionaries (myDict) as a dynamically sized table.
	If column names (colList) aren't specified, they will show in random order.
	Author: Thierry Husson - Use it as you want but don't blame me.
	"""
	if not colList: colList = list(myDict[0].keys() if myDict else [])
	myList = [colList] # 1st row = header
	for item in myDict: myList.append([str(item[col] if item[col] is not None else '') for col in colList])
	colSize = [max(map(len,col)) for col in zip(*myList)]
	formatStr = ' | '.join(["{{:<{}}}".format(i) for i in colSize])
	myList.insert(1, ['-' * i for i in colSize]) # Seperating line
	for item in myList: print(formatStr.format(*item))

def getCompartments():
	compartmentList = []
	list_compartments_response = iam_client.list_compartments(
		compartment_id=tenancyOCID,
		compartment_id_in_subtree=True)
	for compartment in list_compartments_response.data:
		compartmentDict = {}
		compartmentDict["ocid"] = compartment.id
		compartmentDict["name"] = compartment.name
		compartmentList.append(compartmentDict)
	return compartmentList

def getAvailabilityDomains():
	availabilityDomainList = []
	list_availability_domains_response = iam_client.list_availability_domains(
    compartment_id=tenancyOCID)
	for ad in list_availability_domains_response.data:
		availabilityDomainDict = {}
		availabilityDomainDict["ocid"] = ad.id
		availabilityDomainDict["name"] = ad.name
		availabilityDomainList.append(availabilityDomainDict)
	return availabilityDomainList

def getBootVolumes():
	bootVolumeList = []
	for compartment in getCompartments():
		for ad in getAvailabilityDomains():
			list_boot_volumes_response = storage_client.list_boot_volumes(
				availability_domain = ad["name"],
				compartment_id = compartment["ocid"])
			for bv in list_boot_volumes_response.data:
				bootVolumeDict = {}
				bootVolumeDict["ocid"] = bv.id
				bootVolumeDict["name"] = bv.display_name
				bootVolumeList.append(bootVolumeDict)
	return bootVolumeList

def getBootVolumesAttachments():
	bootVolumeAttachmentList = []
	for compartment in getCompartments():
		for ad in getAvailabilityDomains():
			list_boot_volume_attachments_response = compute_client.list_boot_volume_attachments(
		   	compartment_id=compartment["ocid"],
		   	availability_domain = ad["name"])
			for bvAtt in list_boot_volume_attachments_response.data:
				bootVolumeAttachmentDict = {}
				bootVolumeAttachmentDict["instance_ocid"] = bvAtt.instance_id
				bootVolumeAttachmentDict["bv_ocid"] = bvAtt.boot_volume_id
				bootVolumeAttachmentList.append(bootVolumeAttachmentDict)
	return bootVolumeAttachmentList

def getUnattachedVolumes(allVolumes, attachedVolumes):
	unattachedVolumes = []
	for vol in allVolumes:
		if vol not in attachedVolumes:
			unattachedVolumes.append(vol)
	return unattachedVolumes

def extractFromDict(inputList, key):
	"""
	This function takes a list of dictionaries and returns a list of strings corresponding to the specified key
	"""
	res = [elem[key] for elem in inputList]
	return res

allVolumes = getBootVolumes()
attachedVolumes = getBootVolumesAttachments()
unattachedVolumesList = getUnattachedVolumes(extractFromDict(allVolumes, "ocid"), extractFromDict(attachedVolumes, "bv_ocid"))

unattachedVolumes = []
for d in allVolumes:
	if d["ocid"] in unattachedVolumesList:
		unattachedVolumes.append(d)

print('The following boot volumes are not attached to any instance:\n')
printTable(unattachedVolumes)
print('\nMore info:')
for elem in unattachedVolumes:
	print(f'https://cloud.oracle.com/block-storage/boot-volumes/{elem["ocid"]}')
print('\n')
