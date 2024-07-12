# **oci-utilities**

## Information

This repository contains stand-alone scripts that automate many repetitive tasks
I usually perform in administrating OCI tenancies.

## Network scripts

### create_ipsec.py

This script creates a Site-to-Site VPN IPSec connection using the phase 1 and phase 2 parameters suggested by Oracle in [this guide](https://docs.oracle.com/en-us/iaas/Content/Network/Reference/supportedIPsecparams.htm#commercial).

The script will prompt the user for any mandatory parameter that was not provided to the script by the user as argument.

#### Usage

```
python3 create_ipsec.py -c *Compartment_Name
                        --cpe-ip *CPE_IP
                        --drg-name *DRG_Name
                        --name *IPSec_Name
                        (--static | --policy | --bgp)
                        --route *CIDR_Block [--route *CIDR_Block ...]
                        [--local-route *CIDR_Block [--local-route *CIDR_Block ...]]
                        [--ike { 1 | 2} ]
                        [--asn *ASN]
                        [--inside-interface *CIDR_Block/30 --inside-interface *CIDR_Block/30]
                        [--outside-interface *CIDR_Block/30 --outside-interface *CIDR_Block/30]
```
#### Arguments

* `--compartment-id` or `-C` is used to specify the compartment in which the IPSec connection will be created and where the DRG and the CPE are located. It is not possible at this stage to create the IPSec connection in compartment _A_ while the other resources are in compartment _B_.
* `--compartment-name` or `-c` is used to specify the compartment in which the IPSec connection will be created and where the DRG and the CPE are located. It is not possible at this stage to create the IPSec connection in compartment _A_ while the other resources are in compartment _B_.
If both -c and -C are specified, only the OCID will be considered by the program.
* `--cpe-ip` or `-e` is used to specify the IP address of the Customer Premises Endpoint that will be linked to the IPSec connection.
* `--cpe-id` or `-E` is used to specify the OCID of the Customer Premises Endpoint that will be linked to the IPSec connection. If both -e and -E are specified, only the OCID will be considered by the program.
* `--drg-name` or `-g` is used to specify the name of the Dynamic Routing Gateway that will be linked to the IPSec connection.
* `--drg-id` or `-G` is used to specify the OCID of the Dynamic Routing Gateway that will be linked to the IPSec connection. If both -g and -G are specified, only the OCID will be considered by the program.
* `--name` or `-n` is used to specify the name of the IPSec connection.
* `--static`, `--policy` or `--bgp` are used to configure the routing of the two tunnels. One and only one of this options must be used.
* `--route` or `-r` is used to specify a route to the on-premises resources. The use of multiple instances of this parameter is permitted.
* `--local-route` or `-R` is used to specify the OCI routes to advertise. It is only useful while using the `--policy` parameter.
* `--ike` is used to specify the IKE version of the tunnels. The only permitted values are `1` and `2` (which is the default).
* `--asn` is used to specify the Autonomous System Number of the on-premises firewall. It is only useful and required when using the `--bgp` parameter.
* `--inside-interface` is used to specify the ip address inside the tunnel. The use of a /30 CIDR netmask is recommended. It is required when using the `--bgp` parameter. Two instances of this parameter are required, one for each tunnel will be used.
* `--outside-interface` is used to specify the ip address inside the CPE. The use of a /30 CIDR netmask is recommended. It is required when using the `--bgp` parameter. Two instances of this parameter are required, one for each tunnel will be used.

#### Output

When the scripts completes, a new IPSec connection that uses the best-practice configurations suggested by Oracle
for Phase 1 and 2 will be created in the specified compartment of the OCI tenancy.

The script also prints the IPSec configuration. Provide the configuration to a network architect to help them correctly set-up the onpremise firewall.

## Storage scripts

### find_unattached_block_volumes.py

This script checks for block volumes that are unattached to any instance.

This script is meant to be ran periodically to check for block volumes that are unintentionally unattached.

#### Usage

```
python3 find_unattached_block_volumes.py
```

#### Arguments

No arguments shall be provided to the script.

#### Output

The script will print a table detailing the OCID and the name of the unattached block volumes.

The script will also print direct links to the unattached block volumes,
so that the user can view the object details in the OCI console with one click.

#### TODO

* add a `--verbose` mode
* add the ability to terminate the unattached block volumes, with possible flags being: `--terminate-force` `--terminate-ask`

### find_unattached_boot_volumes.py

This script checks for boot volumes that are unattached to any instance.
Any time that a compute instance is terminated, the OCI console prompts the user
asking them if they want to also terminate the boot volumes, but it is easy to miss this prompt
and leave the boot volume unattached.
This script is meant to be ran periodically to check for boot volume that is unintentionally unattached.

#### Usage

```
python3 find_unattached_boot_volumes.py
```

#### Arguments

No arguments shall be provided to the script.

#### Output

The script will print a table detailing the OCID and the name of the unattached boot volumes.

The script will also print direct links to the unattached boot volumes,
so that the user can view the object details in the OCI console with one click.

#### TODO

* add a `--verbose` mode
* add the ability to terminate the unattached boot volumes, with possible flags being: `--terminate-force` `--terminate-ask`