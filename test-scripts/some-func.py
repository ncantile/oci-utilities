#!/bin/python3
import oci

#Create the identity client
config = oci.config.from_file()
iam_client = oci.identity.IdentityClient(config)
tenancyOCID = config["tenancy"]

def getAllDomains():
	"""
	This function retrieves all the IAM Domains in the tenancy.
	It returns a list with the OCIDs of all the domains.
	"""
	domainList = []
	list_domains_response = iam_client.list_domains(
		compartment_id = tenancyOCID,
		lifecycle_state = "ACTIVE")
	for domain in list_domains_response.data:
		domainDict = {}
		domainDict["id"] = domain.id
		domainDict["name"] = domain.display_name
		domainList.append(domainDict)
	return domainList


def getUsersInDomain(domainOCID):
	usersOCIDList = []
	list_users_response = iam_client.list_users(
		compartment_id = tenancyOCID,
		)
	for user in list_users_response.data:
		usersOCIDList.append(user.id)
	return usersOCIDList

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