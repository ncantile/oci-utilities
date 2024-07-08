#!/bin/python3
import oci
import argparse
import sys
import random
import string
import time

parser = argparse.ArgumentParser(description="This program creates a Site-to-site IPSec VPN")
parser.add_argument("--compartment-id", "-c", help="The compartment in which the VPN will be created, specified by its OCID")
parser.add_argument("--cpe-ip", "-e", help="The IP of the CPE object")
parser.add_argument("--cpe-id", "-E", help="The OCID of the CPE object")
parser.add_argument("--best-practices", "-d", action="store_true", help="Use Oracle-suggested set of options for Phase 1 and Phase 2 configuration")
parser.add_argument("--drg-id", "-G", help="The OCID of the Dynamic Routing Gateway")
parser.add_argument("--drg-name", "-g", help="The name of the Dynamic Routing Gateway")
parser.add_argument("--route", "-r", action="append", help="The remote static route used for the IPSec connection. Provide multiple routes by using multiple -r calls")
parser.add_argument("--local-route", "-R", action="append", help="The local route used to configure policy-based routing. Provide multiple routes by using multiple -R calls")
parser.add_argument("--name", "-n", help="The name of the IPSec connection")
parser.add_argument("--static", action="store_true", help="Use tunnels configured with static routing")
parser.add_argument("--policy", action="store_true", help="Use tunnels configured with policy-based routing")
parser.add_argument("--bgp", action="store_true", help="Use tunnels configured with dynamic routing")
parser.add_argument("--ike", "-i", default="2", choices=["1", "2"], help="The IKE version of the tunnels. Defaults to IKEv2")
parser.add_argument("--asn", help="The customer ASN")
parser.add_argument("--inside-interface", "-T", action="append", help="The IP addresses for the OCI end of the inside tunnels interfaces. Defaults to a /30. Provide two routes by using two -T calls" )
parser.add_argument("--outside-interface", "-t", action="append", help="The IP addresses for the CPE end of the inside tunnels interfaces. Defaults to a /30. Provide two routes by using two -t calls" )

args = parser.parse_args()

compartmentOCID = args.compartment_id
cpeIP = args.cpe_ip
cpeOCID = args.cpe_id
isBestPractices = args.best_practices
drgOCID = args.drg_id
drgName = args.drg_name
ipsecRoutes = args.route
ipsecLocalRoutes = args.local_route
ipsecName = args.name
isStatic = args.static
isPolicy = args.policy
isBGP = args.bgp
ikeVer = "V" + args.ike
asn = args.asn
if not args.inside_interface:
    insideIP = []
else:
    insideIP = args.inside_interface
if not args.outside_interface:
    outsideIP = []
else:
    outsideIP = args.outside_interface

def fatalExit(message) -> None:
    print(f"FATAL: {message}")
    sys.exit(1)

core_client = oci.core.VirtualNetworkClient(oci.config.from_file())

if not ipsecName:
    fatalExit("please provide a name for the IPSec connection\n  Use --name")

# Checks if there is one and only one routing policy
if isStatic + isPolicy + isBGP == 0:
    fatalExit("a routing policy must be specified\n  Choose one among --bgp, --policy, --static")   
elif isStatic + isPolicy + isBGP > 1:
    fatalExit("only one routing policy must be specified\n  Choose only one among --bgp, --policy, --static")

# Check if two insideIPs and two outsideIPs are specified for dynamic routing. If --best-practices: automatically assign
if isBGP:
    routingType = "BGP"
    if not asn:
        fatalExit("the customer ASN must be specified\n  Use --asn")
    elif (len(insideIP) != 2 or len(outsideIP) != 2) and not isBestPractices:
        fatalExit("for dynamic routing, one IP per tunnel must be specified as inside and outside tunnel interfaces\n  Use two -t and two -T calls")
    elif len(insideIP) != 2 and len(outsideIP) != 2 and isBestPractices:
        print("INFO: --best-practices specified, using automatic inside IPs")
        insideIP = ["10.0.1.2/30", "10.0.2.2/30"]
        print("INFO: --best-practices specified, using automatic outside IPs")
        outsideIP = ["10.0.1.1/30", "10.0.2.1/30"]

#create logic:
#Get the OCID of the DRG
if not drgOCID and drgName:
    network_client = oci.core.VirtualNetworkClient(oci.config.from_file())
    drgList = network_client.list_drgs(compartment_id=compartmentOCID)
    for drg in drgList.data:
        if drg.display_name == drgName:
            drgOCID = drg.id
            break
        else:
            fatalExit(f"{drgName} not found in the specified compartment")
elif drgOCID:
    pass
else:
    fatalExit("DRG not specified.\n  Use either -G or -g")

#Get the OCID of the CPE
if not cpeOCID and cpeIP:
    network_client = oci.core.VirtualNetworkClient(oci.config.from_file())
    cpeList = network_client.list_cpes(compartment_id=compartmentOCID)
    for cpe in cpeList.data:
        if cpe.ip_address == cpeIP:
            cpeOCID = cpe.id
            break
        else:
            fatalExit(f"No CPE with IP {cpeIP} found in the specified compartment")
elif cpeOCID:
    pass
else:
    fatalExit("CPE not specified.\n  Use either -E or -e")



# Make static routes required or automatically populated
if not ipsecRoutes:
    print("WARNING: no routes provided to on-premise: automatically assigning fake route 1.2.3.4/32")
    ipsecRoutes = ["1.2.3.4/32"]
else:
    pass

# Check if there are both local and remote routes if the IPSec uses policy-based routing
if isPolicy:
    routingType = "POLICY"
    if len(ipsecLocalRoutes) > 0 and len(ipsecRoutes) > 0:
        pass
    else:
        fatalExit("both local and remote routes are needed for policy-based routing\n  Use both -r and -R")
else:
    pass

# Check if there is a route if the IPSec uses static routing
if isStatic:
    routingType = "STATIC"
    if len(ipsecRoutes) > 0:
        pass
    else:
        fatalExit("specify at least a route\n  Use -r")

tunnelNames = ["T1-" + ipsecName, "T2-" + ipsecName]

tunnelSecret = "".join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=64))

if isBestPractices:
    if isStatic:
        create_ip_sec_connection_response = core_client.create_ip_sec_connection(
            create_ip_sec_connection_details=oci.core.models.CreateIPSecConnectionDetails(
                compartment_id=compartmentOCID,
                cpe_id=cpeOCID,
                drg_id=drgOCID,
                static_routes=ipsecRoutes,
                display_name=ipsecName,
                tunnel_configuration=[
                    #Tunnel1
                    oci.core.models.CreateIPSecConnectionTunnelDetails(
                        display_name=tunnelNames[0],
                        routing=routingType,
                        ike_version=ikeVer,
                        shared_secret=tunnelSecret,
                        oracle_initiation="INITIATOR_OR_RESPONDER",
                        nat_translation_enabled="AUTO",
                        phase_one_config=oci.core.models.PhaseOneConfigDetails(
                            is_custom_phase_one_config=True,
                            authentication_algorithm="SHA2_384",
                            encryption_algorithm="AES_256_CBC",
                            diffie_helman_group="GROUP20",
                            lifetime_in_seconds=28800),
                        phase_two_config=oci.core.models.PhaseTwoConfigDetails(
                            is_custom_phase_two_config=True,
                            authentication_algorithm="HMAC_SHA2_256_128",
                            encryption_algorithm="AES_256_GCM",
                            lifetime_in_seconds=3600,
                            is_pfs_enabled=True,
                            pfs_dh_group="GROUP5"),
                        dpd_config=oci.core.models.DpdConfig(
                            dpd_mode="INITIATE_AND_RESPOND",
                            dpd_timeout_in_sec=20)),
                    #Tunnel2
                    oci.core.models.CreateIPSecConnectionTunnelDetails(
                        display_name=tunnelNames[1],
                        routing=routingType,
                        ike_version=ikeVer,
                        shared_secret=tunnelSecret,
                        oracle_initiation="INITIATOR_OR_RESPONDER",
                        nat_translation_enabled="AUTO",
                        phase_one_config=oci.core.models.PhaseOneConfigDetails(
                            is_custom_phase_one_config=True,
                            authentication_algorithm="SHA2_384",
                            encryption_algorithm="AES_256_CBC",
                            diffie_helman_group="GROUP20",
                            lifetime_in_seconds=28800),
                        phase_two_config=oci.core.models.PhaseTwoConfigDetails(
                            is_custom_phase_two_config=True,
                            authentication_algorithm="HMAC_SHA2_256_128",
                            encryption_algorithm="AES_256_GCM",
                            lifetime_in_seconds=3600,
                            is_pfs_enabled=True,
                            pfs_dh_group="GROUP5"),
                        dpd_config=oci.core.models.DpdConfig(
                            dpd_mode="INITIATE_AND_RESPOND",
                            dpd_timeout_in_sec=20))]))
    elif isPolicy:
        create_ip_sec_connection_response = core_client.create_ip_sec_connection(
            create_ip_sec_connection_details=oci.core.models.CreateIPSecConnectionDetails(
                compartment_id=compartmentOCID,
                cpe_id=cpeOCID,
                drg_id=drgOCID,
                static_routes=ipsecRoutes,
                display_name=ipsecName,
                tunnel_configuration=[
                    #Tunnel1
                    oci.core.models.CreateIPSecConnectionTunnelDetails(
                        display_name=tunnelNames[0],
                        routing=routingType,
                        ike_version=ikeVer,
                        shared_secret=tunnelSecret,
                        oracle_initiation="INITIATOR_OR_RESPONDER",
                        nat_translation_enabled="AUTO",
                        phase_one_config=oci.core.models.PhaseOneConfigDetails(
                            is_custom_phase_one_config=True,
                            authentication_algorithm="SHA2_384",
                            encryption_algorithm="AES_256_CBC",
                            diffie_helman_group="GROUP20",
                            lifetime_in_seconds=28800),
                        phase_two_config=oci.core.models.PhaseTwoConfigDetails(
                            is_custom_phase_two_config=True,
                            authentication_algorithm="HMAC_SHA2_256_128",
                            encryption_algorithm="AES_256_GCM",
                            lifetime_in_seconds=3600,
                            is_pfs_enabled=True,
                            pfs_dh_group="GROUP5"),
                        encryption_domain_config=oci.core.models.CreateIPSecTunnelEncryptionDomainDetails(
                            oracle_traffic_selector=ipsecLocalRoutes,
                            cpe_traffic_selector=ipsecRoutes),
                        dpd_config=oci.core.models.DpdConfig(
                            dpd_mode="INITIATE_AND_RESPOND",
                            dpd_timeout_in_sec=20)),
                    #Tunnel2
                    oci.core.models.CreateIPSecConnectionTunnelDetails(
                        display_name=tunnelNames[1],
                        routing=routingType,
                        ike_version=ikeVer,
                        shared_secret=tunnelSecret,
                        oracle_initiation="INITIATOR_OR_RESPONDER",
                        nat_translation_enabled="AUTO",
                        phase_one_config=oci.core.models.PhaseOneConfigDetails(
                            is_custom_phase_one_config=True,
                            authentication_algorithm="SHA2_384",
                            encryption_algorithm="AES_256_CBC",
                            diffie_helman_group="GROUP20",
                            lifetime_in_seconds=28800),
                        phase_two_config=oci.core.models.PhaseTwoConfigDetails(
                            is_custom_phase_two_config=True,
                            authentication_algorithm="HMAC_SHA2_256_128",
                            encryption_algorithm="AES_256_GCM",
                            lifetime_in_seconds=3600,
                            is_pfs_enabled=True,
                            pfs_dh_group="GROUP5"),
                        encryption_domain_config=oci.core.models.CreateIPSecTunnelEncryptionDomainDetails(
                            oracle_traffic_selector=ipsecLocalRoutes,
                            cpe_traffic_selector=ipsecRoutes),
                        dpd_config=oci.core.models.DpdConfig(
                            dpd_mode="INITIATE_AND_RESPOND",
                            dpd_timeout_in_sec=20))]))
    elif isBGP:
        create_ip_sec_connection_response = core_client.create_ip_sec_connection(
            create_ip_sec_connection_details=oci.core.models.CreateIPSecConnectionDetails(
                compartment_id=compartmentOCID,
                cpe_id=cpeOCID,
                drg_id=drgOCID,
                static_routes=ipsecRoutes,
                display_name=ipsecName,
                tunnel_configuration=[
                    #Tunnel1
                    oci.core.models.CreateIPSecConnectionTunnelDetails(
                        display_name=tunnelNames[0],
                        routing=routingType,
                        ike_version=ikeVer,
                        shared_secret=tunnelSecret,
                        bgp_session_config=oci.core.models.CreateIPSecTunnelBgpSessionDetails(
                            oracle_interface_ip=insideIP[0],
                            customer_interface_ip=outsideIP[0],
                            customer_bgp_asn=asn),
                        oracle_initiation="INITIATOR_OR_RESPONDER",
                        nat_translation_enabled="AUTO",
                        phase_one_config=oci.core.models.PhaseOneConfigDetails(
                            is_custom_phase_one_config=True,
                            authentication_algorithm="SHA2_384",
                            encryption_algorithm="AES_256_CBC",
                            diffie_helman_group="GROUP20",
                            lifetime_in_seconds=28800),
                        phase_two_config=oci.core.models.PhaseTwoConfigDetails(
                            is_custom_phase_two_config=True,
                            authentication_algorithm="HMAC_SHA2_256_128",
                            encryption_algorithm="AES_256_GCM",
                            lifetime_in_seconds=3600,
                            is_pfs_enabled=True,
                            pfs_dh_group="GROUP5"),
                        dpd_config=oci.core.models.DpdConfig(
                            dpd_mode="INITIATE_AND_RESPOND",
                            dpd_timeout_in_sec=20)),
                    #Tunnel2
                    oci.core.models.CreateIPSecConnectionTunnelDetails(
                        display_name=tunnelNames[1],
                        routing=routingType,
                        ike_version=ikeVer,
                        shared_secret=tunnelSecret,
                        bgp_session_config=oci.core.models.CreateIPSecTunnelBgpSessionDetails(
                            oracle_interface_ip=insideIP[1],
                            customer_interface_ip=outsideIP[1],
                            customer_bgp_asn=asn),
                        oracle_initiation="INITIATOR_OR_RESPONDER",
                        nat_translation_enabled="AUTO",
                        phase_one_config=oci.core.models.PhaseOneConfigDetails(
                            is_custom_phase_one_config=True,
                            authentication_algorithm="SHA2_384",
                            encryption_algorithm="AES_256_CBC",
                            diffie_helman_group="GROUP20",
                            lifetime_in_seconds=28800),
                        phase_two_config=oci.core.models.PhaseTwoConfigDetails(
                            is_custom_phase_two_config=True,
                            authentication_algorithm="HMAC_SHA2_256_128",
                            encryption_algorithm="AES_256_GCM",
                            lifetime_in_seconds=3600,
                            is_pfs_enabled=True,
                            pfs_dh_group="GROUP5"),
                        dpd_config=oci.core.models.DpdConfig(
                            dpd_mode="INITIATE_AND_RESPOND",
                            dpd_timeout_in_sec=20))]))
else:
    if isStatic:
        create_ip_sec_connection_response = core_client.create_ip_sec_connection(
            create_ip_sec_connection_details=oci.core.models.CreateIPSecConnectionDetails(
                compartment_id=compartmentOCID,
                cpe_id=cpeOCID,
                drg_id=drgOCID,
                static_routes=ipsecRoutes,
                display_name=ipsecName,
                tunnel_configuration=[
                    #Tunnel1
                    oci.core.models.CreateIPSecConnectionTunnelDetails(
                        display_name=tunnelNames[0],
                        routing=routingType,
                        ike_version=ikeVer,
                        shared_secret=tunnelSecret,
                        oracle_initiation="INITIATOR_OR_RESPONDER",
                        nat_translation_enabled="AUTO",
                        dpd_config=oci.core.models.DpdConfig(
                            dpd_mode="INITIATE_AND_RESPOND",
                            dpd_timeout_in_sec=20)),
                    #Tunnel2
                    oci.core.models.CreateIPSecConnectionTunnelDetails(
                        display_name=tunnelNames[1],
                        routing=routingType,
                        ike_version=ikeVer,
                        shared_secret=tunnelSecret,
                        oracle_initiation="INITIATOR_OR_RESPONDER",
                        nat_translation_enabled="AUTO",
                        dpd_config=oci.core.models.DpdConfig(
                            dpd_mode="INITIATE_AND_RESPOND",
                            dpd_timeout_in_sec=20))]))
    elif isPolicy:
        create_ip_sec_connection_response = core_client.create_ip_sec_connection(
            create_ip_sec_connection_details=oci.core.models.CreateIPSecConnectionDetails(
                compartment_id=compartmentOCID,
                cpe_id=cpeOCID,
                drg_id=drgOCID,
                static_routes=ipsecRoutes,
                display_name=ipsecName,
                tunnel_configuration=[
                    #Tunnel1
                    oci.core.models.CreateIPSecConnectionTunnelDetails(
                        display_name=tunnelNames[0],
                        routing=routingType,
                        ike_version=ikeVer,
                        shared_secret=tunnelSecret,
                        oracle_initiation="INITIATOR_OR_RESPONDER",
                        nat_translation_enabled="AUTO",
                        encryption_domain_config=oci.core.models.CreateIPSecTunnelEncryptionDomainDetails(
                            oracle_traffic_selector=ipsecLocalRoutes,
                            cpe_traffic_selector=ipsecRoutes),
                        dpd_config=oci.core.models.DpdConfig(
                            dpd_mode="INITIATE_AND_RESPOND",
                            dpd_timeout_in_sec=20)),
                    #Tunnel2
                    oci.core.models.CreateIPSecConnectionTunnelDetails(
                        display_name=tunnelNames[1],
                        routing=routingType,
                        ike_version=ikeVer,
                        shared_secret=tunnelSecret,
                        oracle_initiation="INITIATOR_OR_RESPONDER",
                        nat_translation_enabled="AUTO",
                        encryption_domain_config=oci.core.models.CreateIPSecTunnelEncryptionDomainDetails(
                            oracle_traffic_selector=ipsecLocalRoutes,
                            cpe_traffic_selector=ipsecRoutes),
                        dpd_config=oci.core.models.DpdConfig(
                            dpd_mode="INITIATE_AND_RESPOND",
                            dpd_timeout_in_sec=20))]))
    elif isBGP:
        create_ip_sec_connection_response = core_client.create_ip_sec_connection(
            create_ip_sec_connection_details=oci.core.models.CreateIPSecConnectionDetails(
                compartment_id=compartmentOCID,
                cpe_id=cpeOCID,
                drg_id=drgOCID,
                static_routes=ipsecRoutes,
                display_name=ipsecName,
                tunnel_configuration=[
                    #Tunnel1
                    oci.core.models.CreateIPSecConnectionTunnelDetails(
                        display_name=tunnelNames[0],
                        routing=routingType,
                        ike_version=ikeVer,
                        shared_secret=tunnelSecret,
                        bgp_session_config=oci.core.models.CreateIPSecTunnelBgpSessionDetails(
                            oracle_interface_ip=insideIP[0],
                            customer_interface_ip=outsideIP[0],
                            customer_bgp_asn=asn),
                        oracle_initiation="INITIATOR_OR_RESPONDER",
                        nat_translation_enabled="AUTO",
                        dpd_config=oci.core.models.DpdConfig(
                            dpd_mode="INITIATE_AND_RESPOND",
                            dpd_timeout_in_sec=20)),
                    #Tunnel2
                    oci.core.models.CreateIPSecConnectionTunnelDetails(
                        display_name=tunnelNames[1],
                        routing=routingType,
                        ike_version=ikeVer,
                        shared_secret=tunnelSecret,
                        bgp_session_config=oci.core.models.CreateIPSecTunnelBgpSessionDetails(
                            oracle_interface_ip=insideIP[1],
                            customer_interface_ip=outsideIP[1],
                            customer_bgp_asn=asn),
                        oracle_initiation="INITIATOR_OR_RESPONDER",
                        nat_translation_enabled="AUTO",
                        dpd_config=oci.core.models.DpdConfig(
                            dpd_mode="INITIATE_AND_RESPOND",
                            dpd_timeout_in_sec=20))]))

# Get the data from response
ipsecOCID = create_ip_sec_connection_response.data.id
print(type(ipsecOCID))
# ipsecInfo = core_client.get_ip_sec_connection(ipsecOCID).data

# #Check the lifecycle state of the ipsec
# for _ in range(1,10):
#     #Check the lifecycle state of the ipsec
#     ipsecLifecycle = ipsecInfo.lifecycle_state
#     if ipsecLifecycle.upper() == 'AVAILABLE':
#         print(f'SUCCESS!\n  IPSec {ipsecName} successfully created.')
#         break
#     elif ipsecLifecycle.upper() == 'PROVISIONING':
#         print(f'IPSec {ipsecName} still in \'provisioning\' state, checking again in 10 seconds...')
#         time.sleep(10)
#     else:
#         print(f'ERROR: IPSec {ipsecName} has some problems, please check manually')
#         sys.exit(1)
# else:
#     print(f'ERROR: IPSec {ipsecName} has some problems, please check manually')
#     sys.exit(1)

# print(ipsecInfo)
